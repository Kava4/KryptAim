"""Main AI loop orchestrating capture, inference, aim, and trigger."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

from Config.app_identity import is_beta_channel
from Config.config_manager import ensure_ai_bin_dirs, get_ai_configs_dir, load_config
from Makcu.makcu_manager import makcu_manager
from Recoil.hotkeys import HotkeyValidationError, is_hotkey_pressed, normalize_hotkey_string, validate_hotkey_bindings

from AI.Engine.aim import AimController
from AI.Engine.capture import ScreenCapture
from AI.Engine.inference import OnnxDetector
from AI.Engine.models import list_local_models, resolve_model_path
from AI.Engine.prediction import KalmanPredictor, ShalloePredictor
from AI.Engine.settings import AiSettings
from AI.Engine.target import TargetSelector
from AI.Engine.trigger import TriggerController

logger = logging.getLogger('AimSync.AI.Engine')


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


class AiEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.settings = AiSettings()
        self.capture = ScreenCapture()
        self.detector = OnnxDetector()
        self.selector = TargetSelector(self.settings)
        self.trigger = TriggerController(self.settings, self.capture)
        self.status = EngineStatus()
        self._kalman = KalmanPredictor()
        self._shalloe = ShalloePredictor()
        self._prev_x = 0
        self._prev_y = 0
        self._aim: AimController | None = None
        self._loaded_model = ''
        self._load_attempted = ''
        self._config_signature = ''

    def _aim_key_active(self, config: dict) -> bool:
        if self.settings.toggles['Constant AI Tracking']:
            return True
        for key in ('ai_aim_keybind', 'ai_second_aim_keybind'):
            if is_hotkey_pressed(config.get(key, 'None')):
                return True
        return False

    def _should_process(self) -> bool:
        return (
            self.settings.toggles['Aim Assist']
            or self.settings.toggles['Auto Trigger']
        )

    def _should_predict(self, config: dict) -> bool:
        return self._aim_key_active(config) or self.settings.toggles.get('Constant AI Tracking', False)

    def invalidate_load_cache(self) -> None:
        self._load_attempted = ''
        self._config_signature = ''

    def reload_from_config(self) -> None:
        config = load_config()
        self.status.enabled = bool(config.get('ai_engine_enabled'))
        self.status.active_config = config.get('ai_active_config', 'Default.cfg') or 'Default.cfg'
        desired_model = (config.get('ai_active_model', '') or '').strip()

        cfg_path = config.get('ai_active_config', 'Default.cfg')
        signature = f'{desired_model}|{cfg_path}|{self.status.enabled}'
        if signature == self._config_signature and desired_model == self._load_attempted:
            return
        self._config_signature = signature

        self.settings.load_cfg(cfg_path)

        if not desired_model:
            self.detector.unload()
            self._loaded_model = ''
            self._load_attempted = ''
            self.status.model_loaded = False
            self.status.active_model = ''
            self.status.last_error = ''
        elif desired_model != self._loaded_model:
            if desired_model == self._load_attempted and not self.status.model_loaded:
                return
            self._load_attempted = desired_model
            path = resolve_model_path(desired_model)
            if path:
                if self.detector.load(path):
                    self._loaded_model = desired_model
                    self.status.active_model = desired_model
                    self.status.model_loaded = True
                    self.status.last_error = ''
                else:
                    self.status.model_loaded = False
                    self.status.active_model = desired_model
                    detail = self.detector.last_error or 'unknown error'
                    self.status.last_error = f'Failed to load {desired_model}: {detail}'
            else:
                self.status.model_loaded = False
                self.status.active_model = desired_model
                self.status.last_error = f'Model file not found: {desired_model}'

        self._aim = AimController(self.settings, self.capture.screen_width, self.capture.screen_height)

    def start(self) -> None:
        if not is_beta_channel():
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            ensure_ai_bin_dirs()
            from AI.Engine.settings import AiSettings as _AiSettings

            default_cfg = get_ai_configs_dir() / 'Default.cfg'
            if not default_cfg.is_file():
                _AiSettings().save_cfg('Default.cfg')
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name='AiEngine', daemon=True)
            self._thread.start()
            self.status.running = True

    def stop(self) -> None:
        self._stop.set()
        self.trigger.reset_spray()
        with self._lock:
            self.status.running = False

    def _loop(self) -> None:
        logger.info('AI engine thread started.')
        last_status_poll = 0.0
        frame_times: list[float] = []

        while not self._stop.is_set():
            try:
                now = time.time()
                if now - last_status_poll > 2.0:
                    self.reload_from_config()
                    last_status_poll = now

                config = load_config()
                if not config.get('ai_engine_enabled') or not self.status.model_loaded:
                    time.sleep(0.05)
                    continue

                if not self._should_process():
                    time.sleep(0.01)
                    continue

                if not self._should_predict(config):
                    self.trigger.reset_spray()
                    time.sleep(0.005)
                    continue

                if not self.detector.is_loaded or self._aim is None:
                    time.sleep(0.05)
                    continue

                info = self.detector.info
                image_size = info.image_size if info else self.settings.image_size()
                use_mouse = self.settings.dropdowns.get('Detection Area Type') == 'Closest to Mouse'
                region = self.capture.detection_region(image_size, use_mouse)
                rgb = self.capture.grab_rgb(region, image_size)
                if rgb is None:
                    time.sleep(0.01)
                    continue

                output = self.detector.run(rgb)
                if output is None:
                    time.sleep(0.01)
                    continue

                target = self.selector.select(
                    output,
                    region,
                    image_size,
                    info.num_detections if info else 8400,
                )

                aim_active = self._aim_key_active(config)
                self.trigger.run_trigger(target, aim_active)

                if target and self.settings.toggles['Aim Assist'] and aim_active:
                    self.status.last_confidence = target.confidence
                    move_x, move_y = self._aim.compute_move(target)

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
                        half_w = self.capture.screen_width // 2
                        half_h = self.capture.screen_height // 2
                        move_x = screen_x - half_w
                        move_y = screen_y - half_h
                        self._prev_x, self._prev_y = screen_x, screen_y

                    if move_x or move_y:
                        makcu_manager.move(move_x, move_y)

                self.status.iterations += 1
                frame_times.append(time.time())
                frame_times = [t for t in frame_times if time.time() - t < 1.0]
                if len(frame_times) > 1:
                    self.status.fps = len(frame_times) / max(frame_times[-1] - frame_times[0], 0.001)

            except Exception as exc:
                self.status.last_error = str(exc)
                logger.exception('AI engine loop error')
                time.sleep(0.1)

        self.detector.unload()
        logger.info('AI engine thread stopped.')

    def get_status_dict(self) -> dict:
        config = load_config()
        configured_model = (config.get('ai_active_model') or '').strip()
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
        }


_engine: AiEngine | None = None


def get_ai_engine() -> AiEngine:
    global _engine
    if _engine is None:
        _engine = AiEngine()
    return _engine


def start_ai_engine_thread() -> None:
    if is_beta_channel():
        get_ai_engine().start()


def stop_ai_engine() -> None:
    if _engine is not None:
        _engine.stop()
