"""Main AI loop orchestrating capture, inference, aim, and trigger."""

from __future__ import annotations

import logging
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any

from Config.config_manager import ensure_ai_bin_dirs, get_ai_configs_dir, load_config
from Makcu.makcu_manager import makcu_manager
from Recoil.hotkeys import HotkeyValidationError, is_hotkey_pressed, normalize_hotkey_string, validate_hotkey_bindings

from AI.Engine.aim import AimController
from AI.Engine.debug_preview import DebugFrameStore, render_debug_frame, show_cv2_window
from AI.Engine.movement.executor import MovementExecutor, smooth_movement_loop
from AI.Engine.capture_backend import CaptureBackend
from AI.Engine.inference import OnnxDetector
from AI.Engine.inference_backend import (
    backend_for_model,
    create_detector,
    normalize_backend,
    probe_gpu_status,
    uses_ultralytics,
)
from AI.Engine.models import list_local_models, resolve_model_path
from AI.Engine.prediction import KalmanPredictor, ShalloePredictor
from AI.Engine.settings import AiSettings
from AI.Engine.target import TargetSelector
from AI.Engine.class_names import class_details, class_name_list
from AI.Engine.button_mask import mask_indices_from_config, mask_manager_tick
from AI.Engine.profile_sync import apply_config_globals, effective_region_size
from AI.Engine.readiness import build_readiness
from AI.Engine.trigger import TriggerController

logger = logging.getLogger('AimSync.AI.Engine')


def _is_ultralytics_detector(detector: object | None) -> bool:
    """Duck-type check without importing ultralytics/torch at app startup (smaller PyInstaller build)."""
    return type(detector).__name__ == 'UltralyticsDetector'


@dataclass
class EngineStatus:
    running: bool = False
    enabled: bool = False
    model_loaded: bool = False
    active_model: str = ''
    active_config: str = ''
    last_confidence: float = 0.0
    last_error: str = ''
    iterations: int = 0
    fps: float = 0.0
    inference_backend: str = 'directml'
    active_provider: str = ''
    capture_mode: str = 'mss'
    model_loading: bool = False


class AiEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.settings = AiSettings()
        self.capture = CaptureBackend()
        self.detector: OnnxDetector | Any | None = None
        self.selector = TargetSelector(self.settings)
        self.trigger = TriggerController(self.settings, self.capture._mss)
        self.status = EngineStatus()
        self._kalman = KalmanPredictor()
        self._shalloe = ShalloePredictor()
        self._prev_x = 0
        self._prev_y = 0
        self._aim: AimController | None = None
        self._smooth_queue: queue.Queue = queue.Queue(maxsize=48)
        self._movement = MovementExecutor(self._smooth_queue)
        self._smooth_thread: threading.Thread | None = None
        self._debug_store = DebugFrameStore()
        self._loaded_model = ''
        self._load_attempted = ''
        self._config_signature = ''
        self._backend = 'directml'
        self._last_debug_render = 0.0
        self._reload_event = threading.Event()
        self._load_done = threading.Event()
        self._load_done.set()
        self._ndi_refresh_event = threading.Event()
        self._ndi_refresh_done = threading.Event()
        self._ndi_refresh_done.set()
        self._explicit_model_load = False
        self._gpu_cache: dict = {}
        self._gpu_cache_at = 0.0

    def _aim_key_active(self, config: dict) -> bool:
        if config.get('ai_always_on_aim') or self.settings.toggles['Constant AI Tracking']:
            return True
        for key in ('ai_aim_keybind', 'ai_second_aim_keybind'):
            if is_hotkey_pressed(config.get(key, 'None')):
                return True
        return False

    def _dynamic_fov_active(self, config: dict, aim_active: bool) -> bool:
        if not self.settings.toggles.get('Dynamic FOV', False):
            return False
        key = (config.get('ai_dynamic_fov_keybind') or 'None').strip()
        if key.lower() != 'none':
            return is_hotkey_pressed(key)
        return aim_active

    def _trigger_key_active(self, config: dict, aim_active: bool) -> bool:
        if config.get('ai_trigger_always_on'):
            return True
        trigger_key = (config.get('ai_trigger_keybind') or 'None').strip()
        if trigger_key.lower() != 'none' and is_hotkey_pressed(trigger_key):
            return True
        return aim_active

    def _should_process(self, config: dict | None = None) -> bool:
        cfg = config or {}
        return (
            self.settings.toggles['Aim Assist']
            or self.settings.toggles['Auto Trigger']
            or bool(cfg.get('ai_trigger_always_on'))
        )

    def _should_predict(self, config: dict) -> bool:
        aim = self._aim_key_active(config)
        return aim or self._trigger_key_active(config, aim)

    def invalidate_load_cache(self) -> None:
        self._load_attempted = ''
        self._config_signature = ''

    def request_model_load(self) -> None:
        """Allow YOLO/CUDA load even when AI engine toggle is off (model picker)."""
        self._explicit_model_load = True

    def _refresh_gpu_cache(self, *, import_torch: bool = False) -> None:
        if threading.current_thread().name != 'AiEngine':
            return
        try:
            self._gpu_cache = probe_gpu_status(import_torch=import_torch)
            self._gpu_cache_at = time.time()
        except Exception:
            logger.exception('GPU probe failed')

    def _refresh_gpu_cache_after_model_load(self) -> None:
        """Full torch.cuda probe only after YOLO import succeeded (PyInstaller-safe)."""
        self._refresh_gpu_cache(import_torch=True)

    def get_gpu_status(self) -> dict:
        return dict(self._gpu_cache) if self._gpu_cache else {
            'cuda_available': False,
            'cuda_device_name': '',
            'torch_version': '',
            'onnx_providers': [],
            'tensorrt_available': False,
        }

    def refresh_ndi_sources_sync(self, timeout: float = 15.0) -> list[str]:
        """NDI finder must run on AiEngine thread (cyndilib is not Flask-thread safe)."""
        if threading.current_thread().name == 'AiEngine':
            return self.capture.list_ndi_sources(force_refresh=True)
        self._ndi_refresh_done.clear()
        self._ndi_refresh_event.set()
        if not self._ndi_refresh_done.wait(timeout):
            logger.warning('NDI refresh timed out after %.0fs', timeout)
        return list(self.capture._ndi_sources_cache)

    def _should_load_model_weights(self, config: dict) -> bool:
        if not (config.get('ai_active_model') or '').strip():
            return False
        if self._explicit_model_load:
            return True
        return bool(config.get('ai_engine_enabled'))

    def request_reload(self, wait_timeout: float = 0) -> bool:
        """Queue config/model reload on the AI engine thread (CUDA-safe)."""
        if threading.current_thread().name == 'AiEngine':
            self.reload_from_config()
            return True
        self._load_done.clear()
        self._reload_event.set()
        if wait_timeout <= 0:
            return True
        return self._load_done.wait(wait_timeout)

    def reload_from_config(self) -> None:
        with self._lock:
            self._reload_from_config_locked()

    def _reload_from_config_locked(self) -> None:
        try:
            self._apply_reload_from_config()
        finally:
            self._load_done.set()

    def _apply_reload_from_config(self) -> None:
        config = load_config()
        self._refresh_gpu_cache(import_torch=False)
        self.status.enabled = bool(config.get('ai_engine_enabled'))
        self.status.active_config = config.get('ai_active_config', 'Default.cfg') or 'Default.cfg'
        self.status.inference_backend = normalize_backend(config.get('ai_inference_backend'))
        self.status.capture_mode = (config.get('ai_capture_mode') or 'mss').strip().lower()
        self._backend = self.status.inference_backend

        self.capture.configure(
            mode=self.status.capture_mode,
            ndi_source=config.get('ai_ndi_source', ''),
            main_pc_width=int(config.get('ai_main_pc_width', 1920) or 1920),
            main_pc_height=int(config.get('ai_main_pc_height', 1080) or 1080),
        )

        desired_model = (config.get('ai_active_model', '') or '').strip()
        cfg_path = config.get('ai_active_config', 'Default.cfg')
        signature = (
            f'{desired_model}|{cfg_path}|{self.status.enabled}|{self._backend}|'
            f'{self.status.capture_mode}|{config.get("ai_ndi_source", "")}|'
            f'{config.get("ai_main_pc_width")}|{config.get("ai_main_pc_height")}'
        )
        if signature == self._config_signature and desired_model == self._load_attempted:
            apply_config_globals(self.settings, config)
            self._apply_runtime_detector_settings(config)
            return
        self._config_signature = signature

        self.settings.load_cfg(cfg_path)
        apply_config_globals(self.settings, config)

        if not desired_model:
            if self.detector is not None:
                self.detector.unload()
            self.detector = None
            self._loaded_model = ''
            self._load_attempted = ''
            self.status.model_loaded = False
            self.status.active_model = ''
            self.status.active_provider = ''
            self.status.last_error = ''
        elif desired_model != self._loaded_model:
            if desired_model == self._load_attempted and not self.status.model_loaded:
                return
            if not self._should_load_model_weights(config):
                self.status.active_model = desired_model
                self.status.model_loaded = False
                self.status.last_error = ''
                self._load_attempted = ''
                return
            self._load_attempted = desired_model
            path = resolve_model_path(desired_model)
            if path:
                self.status.model_loading = True
                try:
                    backend = backend_for_model(path, self._backend)
                    logger.info('Loading model %s via %s (%s)', desired_model, backend, path)
                    if self.detector is not None:
                        self.detector.unload()
                    self.detector = create_detector(backend)
                    if self.detector.load(path):
                        self._loaded_model = desired_model
                        self.status.active_model = desired_model
                        self.status.model_loaded = True
                        self.status.inference_backend = backend
                        self.status.active_provider = getattr(self.detector, 'active_provider', backend)
                        self.status.last_error = ''
                        self._apply_runtime_detector_settings(config)
                        self._apply_default_player_class(config)
                        self._explicit_model_load = False
                        if _is_ultralytics_detector(self.detector):
                            self._refresh_gpu_cache_after_model_load()
                    else:
                        self.status.model_loaded = False
                        self.status.active_model = desired_model
                        detail = self.detector.last_error or 'unknown error'
                        self.status.last_error = f'Failed to load {desired_model}: {detail}'
                        logger.error('Model load failed: %s', self.status.last_error)
                except Exception:
                    logger.exception('Model load crashed for %s', desired_model)
                    self.status.model_loaded = False
                    self.status.last_error = f'Failed to load {desired_model}: internal error (see log)'
                finally:
                    self.status.model_loading = False
            else:
                self.status.model_loaded = False
                self.status.active_model = desired_model
                self.status.last_error = f'Model file not found: {desired_model}'
                self.status.model_loading = False
        else:
            self._apply_runtime_detector_settings(config)

        sw = self.capture.screen_width
        sh = self.capture.screen_height
        self._aim = AimController(self.settings, sw, sh)

    def _apply_default_player_class(self, config: dict) -> None:
        """Default target class when unset (pick enemy label for CS2-style models)."""
        if (config.get('ai_player_class') or '').strip():
            return
        if self.detector is None:
            return
        names = getattr(self.detector, 'class_names', None) or {}
        if not names:
            return
        from Config.config_manager import load_config, save_config

        labels = class_name_list(names)
        exclude_friendly = (config.get('ai_class_filter_mode') or 'target_label') == 'exclude_friendly'
        pick = labels[0]
        if exclude_friendly:
            for name in labels:
                if name.upper() == 'CT':
                    pick = name
                    break
        else:
            for name in labels:
                if name.upper() == 'T':
                    pick = name
                    break
        config = load_config()
        config['ai_player_class'] = pick
        if not (config.get('ai_head_class') or '').strip() and len(labels) > 1:
            for name in labels:
                alt = name.upper()
                if exclude_friendly and alt == 'T':
                    config['ai_head_class'] = name
                    break
                if not exclude_friendly and alt == 'CT':
                    config['ai_head_class'] = name
                    break
        save_config(config)
        logger.info('Default player class: %s, head: %s', config.get('ai_player_class'), config.get('ai_head_class'))

    def _ndi_connected(self) -> bool:
        return self.status.capture_mode == 'ndi' and self.capture._ndi.connected

    def get_debug_jpeg(self) -> bytes | None:
        return self._debug_store.get_jpeg()

    def _apply_runtime_detector_settings(self, config: dict) -> None:
        if self.detector is None:
            return
        conf = float(config.get('ai_detection_conf', 0.25))
        imgsz = int(config.get('ai_imgsz', 640))
        max_det = int(config.get('ai_max_detect', 50))
        if _is_ultralytics_detector(self.detector):
            self.detector.configure_runtime(conf=conf, imgsz=imgsz, max_det=max_det)

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            ensure_ai_bin_dirs()
            # Bootstrap capture/NDI on the engine thread (avoid CUDA model load on Flask/main thread).
            try:
                config = load_config()
                self.capture.configure(
                    mode=(config.get('ai_capture_mode') or 'ndi').strip().lower(),
                    ndi_source=config.get('ai_ndi_source', ''),
                    main_pc_width=int(config.get('ai_main_pc_width', 1920) or 1920),
                    main_pc_height=int(config.get('ai_main_pc_height', 1080) or 1080),
                )
            except Exception:
                logger.exception('AI engine bootstrap failed')
            self._reload_event.set()
            self._ndi_refresh_event.set()
            from AI.Engine.settings import AiSettings as _AiSettings

            default_cfg = get_ai_configs_dir() / 'Default.cfg'
            if not default_cfg.is_file():
                _AiSettings().save_cfg('Default.cfg')
            self._stop.clear()
            if self._smooth_thread is None or not self._smooth_thread.is_alive():
                self._smooth_thread = threading.Thread(
                    target=smooth_movement_loop,
                    args=(self._stop, self._smooth_queue),
                    name='AiSmoothMove',
                    daemon=True,
                )
                self._smooth_thread.start()
            self._thread = threading.Thread(target=self._loop, name='AiEngine', daemon=True)
            self._thread.start()
            self.status.running = True

    def stop(self) -> None:
        self._stop.set()
        makcu_manager.apply_button_mask([], False)
        self.trigger.reset_spray()
        self.capture.stop()
        show_cv2_window(None, False)
        self._debug_store.set_jpeg(None)
        while not self._smooth_queue.empty():
            try:
                self._smooth_queue.get_nowait()
            except queue.Empty:
                break
        with self._lock:
            self.status.running = False

    def _run_inference(self, bgr, config: dict):
        if self.detector is None or not self.detector.is_loaded:
            return None, 0, 1

        info = self.detector.info
        image_size = info.image_size if info else self.settings.image_size()
        num_classes = info.num_classes if info else 1

        if _is_ultralytics_detector(self.detector):
            result = self.detector.run(bgr)
            if result is None:
                return None, image_size, num_classes
            output = self.detector.to_yolo_tensor(result)
            num_classes = max(len(self.detector.class_names), 1)
            return output, image_size, num_classes

        rgb = bgr[:, :, ::-1]
        output = self.detector.run(rgb)
        return output, image_size, num_classes

    def _loop(self) -> None:
        logger.info('AI engine thread started.')
        last_status_poll = 0.0
        frame_times: list[float] = []

        while not self._stop.is_set():
            try:
                if self._ndi_refresh_event.is_set():
                    self._ndi_refresh_event.clear()
                    try:
                        self.capture.list_ndi_sources(force_refresh=True)
                    except Exception:
                        logger.exception('NDI refresh failed')
                    finally:
                        self._ndi_refresh_done.set()

                now = time.time()
                if self._reload_event.is_set() or now - last_status_poll > 2.0:
                    if self._reload_event.is_set():
                        self._reload_event.clear()
                    self.reload_from_config()
                    last_status_poll = now

                config = load_config()
                if not config.get('ai_engine_enabled') or not self.status.model_loaded:
                    makcu_manager.apply_button_mask([], False)
                    time.sleep(0.05)
                    continue

                if config.get('ai_button_mask') and self._should_predict(config):
                    mask_manager_tick(
                        makcu_manager,
                        mask_indices_from_config(config),
                        True,
                    )
                else:
                    makcu_manager.apply_button_mask([], False)

                if not self._should_process(config):
                    time.sleep(0.01)
                    continue

                if not self._should_predict(config):
                    makcu_manager.apply_button_mask([], False)
                    self.trigger.reset_spray()
                    time.sleep(0.005)
                    continue

                if self.detector is None or not self.detector.is_loaded or self._aim is None:
                    time.sleep(0.05)
                    continue

                info = self.detector.info
                image_size = info.image_size if info else self.settings.image_size()
                use_mouse = self.settings.dropdowns.get('Detection Area Type') == 'Closest to Mouse'
                frame_ctx = self.capture.grab_frame(image_size, use_mouse)
                if frame_ctx is None:
                    time.sleep(0.01)
                    continue

                output, image_size, num_classes = self._run_inference(frame_ctx.bgr, config)
                if output is None:
                    time.sleep(0.01)
                    continue

                if _is_ultralytics_detector(self.detector):
                    self.status.last_confidence = float(
                        getattr(self.detector, 'last_max_detection_conf', 0.0) or 0.0
                    )

                class_names = getattr(self.detector, 'class_names', None) or {}
                if not isinstance(class_names, dict):
                    class_names = {}

                det_conf = float(config.get('ai_detection_conf', 0.25))
                aim_active = self._aim_key_active(config)
                region = effective_region_size(
                    self.settings,
                    config,
                    use_dynamic=self._dynamic_fov_active(config, aim_active),
                )
                crosshair_x = frame_ctx.crosshair_x
                crosshair_y = frame_ctx.crosshair_y
                exclude_friendly = (config.get('ai_class_filter_mode') or 'exclude_friendly') == 'exclude_friendly'
                target = self.selector.select(
                    output,
                    frame_ctx.region,
                    image_size,
                    output.shape[2] if output is not None else 8400,
                    num_classes=num_classes,
                    class_names=class_names,
                    player_label=str(config.get('ai_player_class', '') or ''),
                    head_label=str(config.get('ai_head_class', '') or ''),
                    player_y_offset=int(config.get('ai_player_y_offset', 0) or 0),
                    min_confidence=det_conf,
                    fov_size=region,
                    exclude_friendly=exclude_friendly,
                )

                trigger_active = self._trigger_key_active(config, aim_active)
                self.trigger.run_trigger(
                    target,
                    trigger_active,
                    config,
                    crosshair_x=crosshair_x,
                    crosshair_y=crosshair_y,
                )

                if target and self.settings.toggles['Aim Assist'] and aim_active:
                    if _is_ultralytics_detector(self.detector):
                        self.status.last_confidence = target.confidence
                    humanize = int(config.get('ai_aim_humanization', 0) or 0)
                    move_x, move_y = self._aim.compute_move(
                        target,
                        crosshair_x=crosshair_x,
                        crosshair_y=crosshair_y,
                        humanization=humanize,
                    )

                    if config.get('ai_phase', 1) >= 2 and self.settings.toggles['Predictions']:
                        method = self.settings.dropdowns.get('Prediction Method', 'Linear')
                        screen_x = int(target.screen_center_x)
                        screen_y = int(target.screen_center_y)
                        if method == 'Kalman Filter':
                            screen_x, screen_y = self._kalman.update(screen_x, screen_y)
                        elif method == "Shall0e's Prediction":
                            screen_x, screen_y = self._shalloe.predict(
                                screen_x, screen_y, self._prev_x, self._prev_y,
                            )
                        move_x = screen_x - crosshair_x
                        move_y = screen_y - crosshair_y
                        self._prev_x, self._prev_y = screen_x, screen_y

                    if move_x or move_y:
                        self._movement.apply(move_x, move_y, config, self.settings)
                elif not _is_ultralytics_detector(self.detector):
                    self.status.last_confidence = 0.0

                want_debug = config.get('ai_debug_preview') or config.get('ai_debug_cv2_window')
                cv2_live = bool(config.get('ai_debug_cv2_window'))
                if want_debug and not cv2_live and (now - self._last_debug_render) < 0.1:
                    want_debug = False
                if want_debug:
                    self._last_debug_render = now
                    jpeg, bgr_overlay = render_debug_frame(
                        frame_ctx.bgr,
                        output,
                        image_size=image_size,
                        num_classes=num_classes,
                        class_names=class_names if isinstance(class_names, dict) else {},
                        settings=self.settings,
                        selector=self.selector,
                        player_label=str(config.get('ai_player_class', '') or ''),
                        head_label=str(config.get('ai_head_class', '') or ''),
                        player_y_offset=int(config.get('ai_player_y_offset', 0) or 0),
                        min_confidence=det_conf,
                        active_target=target,
                        fps=self.status.fps,
                        fov_size=region,
                        crosshair_x=crosshair_x,
                        crosshair_y=crosshair_y,
                        exclude_friendly=exclude_friendly,
                        region=frame_ctx.region,
                    )
                    if config.get('ai_debug_preview'):
                        self._debug_store.set_jpeg(jpeg)
                    if config.get('ai_debug_cv2_window'):
                        show_cv2_window(jpeg, True, bgr=bgr_overlay)
                elif config.get('ai_debug_cv2_window'):
                    show_cv2_window(None, False)

                self.status.iterations += 1
                frame_times.append(time.time())
                frame_times = [t for t in frame_times if time.time() - t < 1.0]
                if len(frame_times) > 1:
                    self.status.fps = len(frame_times) / max(frame_times[-1] - frame_times[0], 0.001)

            except Exception as exc:
                self.status.last_error = str(exc)
                logger.exception('AI engine loop error')
                time.sleep(0.1)

        if self.detector is not None:
            self.detector.unload()
        logger.info('AI engine thread stopped.')

    def get_status_dict(self) -> dict:
        config = load_config()
        configured_model = (config.get('ai_active_model') or '').strip()
        gpu = self.get_gpu_status()
        model_classes: list[str] = []
        model_class_details: list[dict] = []
        if self.detector is not None and self.status.model_loaded:
            names = getattr(self.detector, 'class_names', None) or {}
            if isinstance(names, dict) and names:
                model_class_details = class_details(names)
                model_classes = class_name_list(names)
            elif isinstance(names, list):
                model_classes = [str(v) for v in names]
                model_class_details = [{'id': i, 'name': v} for i, v in enumerate(names)]

        try:
            import onnxruntime  # noqa: F401

            onnx_ready = True
        except ImportError:
            onnx_ready = False

        makcu_connected = makcu_manager.is_hardware() and makcu_manager.is_connected()
        makcu_buttons_live = makcu_connected
        makcu_buttons_pressed = makcu_manager.get_pressed_mouse_buttons() if makcu_buttons_live else []
        aim_key_active = self._aim_key_active(config)
        trigger_key_active = self._trigger_key_active(config, aim_key_active)
        readiness = build_readiness(
            status={
                'makcu_connected': makcu_connected,
                'model_loaded': self.status.model_loaded,
                'model_classes': model_classes,
                'onnx_ready': onnx_ready,
                'inference_backend': self.status.inference_backend,
            },
            settings=self.settings,
        )

        capture_mode = (config.get('ai_capture_mode') or 'ndi').strip().lower()
        ndi_sources: list[str] = []
        ndi_finder_ready = False
        ndi_cyndilib_ok = True
        if capture_mode == 'ndi':
            ndi_sources = list(self.capture._ndi_sources_cache)
            ndi_finder_ready = self.capture._ndi._finder is not None
            ndi_cyndilib_ok = self.capture._ndi.is_available

        return {
            'running': self.status.running,
            'enabled': self.status.enabled,
            'model_loaded': self.status.model_loaded,
            'active_model': self.status.active_model,
            'configured_model': configured_model,
            'active_config': self.status.active_config,
            'last_confidence': round(self.status.last_confidence, 3),
            'last_error': self.status.last_error,
            'iterations': self.status.iterations,
            'fps': round(self.status.fps, 1),
            'models': list_local_models(),
            'makcu_hardware': makcu_manager.is_hardware(),
            'makcu_connected': makcu_manager.is_hardware() and makcu_manager.is_connected(),
            'inference_backend': self.status.inference_backend,
            'active_provider': self.status.active_provider,
            'capture_mode': capture_mode,
            'ndi_sources': ndi_sources,
            'ndi_source_count': len(ndi_sources),
            'ndi_finder_ready': ndi_finder_ready,
            'ndi_cyndilib_ok': ndi_cyndilib_ok if capture_mode == 'ndi' else True,
            'ndi_import_error': self.capture._ndi.import_error if capture_mode == 'ndi' else '',
            'aim_key_active': aim_key_active,
            'trigger_key_active': trigger_key_active,
            'makcu_buttons_live': makcu_buttons_live,
            'makcu_buttons_pressed': makcu_buttons_pressed,
            'aim_assist_on': bool(self.settings.toggles.get('Aim Assist')),
            'auto_trigger_on': bool(self.settings.toggles.get('Auto Trigger')),
            'trigger_always_on': bool(config.get('ai_trigger_always_on')),
            'trigger_last_fire_age_s': round(
                max(0.0, time.time() - self.trigger.last_fire_at), 2,
            ) if self.trigger.last_fire_at else None,
            'trigger_block_reason': self.trigger.last_block_reason or '',
            'portable_build': bool(getattr(sys, 'frozen', False)),
            'cuda_available': gpu.get('cuda_available', False),
            'cuda_device_name': gpu.get('cuda_device_name', ''),
            'torch_version': gpu.get('torch_version', ''),
            'onnx_providers': gpu.get('onnx_providers', []),
            'tensorrt_available': gpu.get('tensorrt_available', False),
            'model_classes': model_classes,
            'model_class_details': model_class_details,
            'model_loading': self.status.model_loading,
            'ai_player_class': config.get('ai_player_class', ''),
            'ai_head_class': config.get('ai_head_class', ''),
            'ai_aim_mode': config.get('ai_aim_mode', 'normal'),
            'movement_mode': self._movement.resolve_mode(config, self.settings),
            'movement_path': self.settings.dropdowns.get('Movement Path', 'Linear'),
            'ai_debug_preview': bool(config.get('ai_debug_preview')),
            'ndi_connected': capture_mode == 'ndi' and self._ndi_connected(),
            'ndi_last_error': self.capture._ndi.last_error if capture_mode == 'ndi' else '',
            'community_models_supported': True,
            'ai_region_size': effective_region_size(self.settings, config),
            'ai_fov_size': effective_region_size(
                self.settings,
                config,
                use_dynamic=self._dynamic_fov_active(config, self._aim_key_active(config)),
            ),
            'ai_dynamic_fov': bool(self.settings.toggles.get('Dynamic FOV', False)),
            'readiness': readiness,
        }


_engine: AiEngine | None = None


def get_ai_engine() -> AiEngine:
    global _engine
    if _engine is None:
        _engine = AiEngine()
    return _engine


def start_ai_engine_thread() -> None:
    get_ai_engine().start()


def stop_ai_engine() -> None:
    if _engine is not None:
        _engine.stop()
