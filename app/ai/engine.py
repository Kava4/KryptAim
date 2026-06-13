"""AI loop — NDI capture, async YOLO, trigger."""

from __future__ import annotations

import threading
import time

from app.ai.aim import AimController, aim_armed
from app.ai.capture import CaptureBackend
from app.ai.capture.backend import FrameContext
from app.ai.inference import YoloDetector
from app.ai.ndi_control import consume_ndi_refresh_request, get_ndi_sources, set_ndi_sources
from app.ai.status import get_ai_runtime_status, update_ai_runtime_status
from app.ai.target_tracker import TargetTracker
from app.ai.targets import predictions_from_detections
from app.ai.trigger import TriggerController, trigger_armed
from app.ai.types import Prediction
from app.core.config import load_config

class AiEngine:
    def __init__(self) -> None:
        self.trigger = TriggerController()
        self.aim = AimController()
        self.capture = CaptureBackend()
        self.detector = YoloDetector()
        self._target_tracker = TargetTracker()
        self._config_loaded_at = 0.0
        self._config_cache: dict | None = None
        self._capture_sig = ''
        self._model_sig = ''
        self._frame_count = 0
        self._fps_t0 = time.perf_counter()
        self._ndi_poll_at = 0.0
        self._ndi_refresh_pending = False
        self._det_lock = threading.Lock()
        self._latest_targets: list[Prediction] = []
        self._latest_frame: FrameContext | None = None
        self._latest_inference_ms = 0.0
        self._latest_det_seq = 0
        self._last_trigger_seq = -1
        self._det_stop = threading.Event()
        self._det_thread: threading.Thread | None = None
        self._det_seq = 0

    def _get_config(self) -> dict:
        now = time.time()
        if self._config_cache is None or (now - self._config_loaded_at) >= 1.0:
            self._config_cache = load_config()
            self._config_loaded_at = now
        return self._config_cache

    def invalidate_config_cache(self) -> None:
        self._config_cache = None

    def start_detection_loop(self) -> None:
        if self._det_thread is not None and self._det_thread.is_alive():
            return
        self._det_stop.clear()
        self._det_thread = threading.Thread(
            target=self._detection_loop,
            name='YoloDetect',
            daemon=True,
        )
        self._det_thread.start()

    def stop(self) -> None:
        self._det_stop.set()
        if self._det_thread is not None:
            self._det_thread.join(timeout=2.0)
            self._det_thread = None
        self.capture.stop()

    def _apply_capture_config(self, config: dict) -> None:
        sig = (
            f"{config.get('ai_ndi_source', '')}|"
            f"{config.get('ai_main_pc_width', 1920)}|"
            f"{config.get('ai_main_pc_height', 1080)}"
        )
        if sig == self._capture_sig:
            return
        self._capture_sig = sig
        self.capture.configure(
            ndi_source=str(config.get('ai_ndi_source', '') or ''),
            main_pc_width=int(config.get('ai_main_pc_width', 1920)),
            main_pc_height=int(config.get('ai_main_pc_height', 1080)),
        )

    def _ensure_model(self, config: dict) -> bool:
        path = str(config.get('ai_model_path', '') or '').strip()
        conf = float(config.get('ai_detection_conf', 0.25))
        player = str(config.get('ai_player_class', '') or '')
        sig = f'{path}|{conf}|{player}'
        if not path:
            self._model_sig = sig
            self.detector.unload()
            return False
        if sig == self._model_sig and self.detector.is_loaded:
            return True
        self._model_sig = sig
        return self.detector.load(path, conf=conf)

    def _update_fps(self) -> float:
        self._frame_count += 1
        elapsed = time.perf_counter() - self._fps_t0
        if elapsed < 1.0:
            return 0.0
        fps = self._frame_count / elapsed
        self._frame_count = 0
        self._fps_t0 = time.perf_counter()
        return fps

    def _get_latest_detection(self) -> tuple[list[Prediction], FrameContext | None, float, int]:
        with self._det_lock:
            return (
                list(self._latest_targets),
                self._latest_frame,
                self._latest_inference_ms,
                self._latest_det_seq,
            )

    def _detection_loop(self) -> None:
        while not self._det_stop.is_set():
            try:
                config = self._get_config()
                if not config.get('ai_enabled'):
                    time.sleep(0.05)
                    continue

                self._apply_capture_config(config)
                image_size = int(config.get('ai_region_size', 640) or 640)
                if not self.capture.ndi.has_video:
                    time.sleep(0.005)
                    continue
                if not self._ensure_model(config):
                    time.sleep(0.05)
                    continue

                frame = self.capture.grab_frame(image_size)
                if frame is None:
                    time.sleep(0.002)
                    continue

                t0 = time.perf_counter()
                raw = self.detector.detect(frame.bgr)
                inference_ms = (time.perf_counter() - t0) * 1000.0
                raw_targets = predictions_from_detections(
                    raw,
                    image_size,
                    player_label=str(config.get('ai_player_class', '') or ''),
                    head_class=str(config.get('ai_head_class', '') or ''),
                    aim_point=str(config.get('ai_aim_point', 'head') or 'head'),
                    model_names=self.detector.class_names,
                )
                trigger_targets = raw_targets
                if config.get('ai_trigger_enabled'):
                    lookahead = float(config.get('ai_trigger_prediction_ms', 35) or 0)
                    if lookahead > 0:
                        trigger_targets = self._target_tracker.apply(
                            raw_targets,
                            image_size=image_size,
                            lookahead_ms=lookahead,
                            inference_ms=inference_ms,
                        )
                else:
                    self._target_tracker.reset()

                if config.get('ai_aim_enabled'):
                    self.aim.update_correction(
                        config,
                        armed=aim_armed(config),
                        targets=raw_targets,
                        frame=frame,
                    )
                else:
                    self.aim.reset_tracking()

                self._det_seq += 1
                with self._det_lock:
                    self._latest_targets = trigger_targets
                    self._latest_frame = frame
                    self._latest_inference_ms = inference_ms
                    self._latest_det_seq = self._det_seq
            except Exception:
                time.sleep(0.01)

    def _publish(
        self,
        config: dict,
        *,
        state: str,
        detail: str,
        armed: bool,
        ndi,
        fps: float = 0.0,
        detections: int = 0,
        inference_ms: float = 0.0,
    ) -> None:
        update_ai_runtime_status(
            state=state,
            detail=detail,
            trigger_armed=armed,
            last_block_reason=self.trigger.last_block_reason,
            aim_block_reason=self.aim.last_block_reason,
            in_zone_count=self.trigger.last_in_zone_count,
            ndi_connected=ndi.connected,
            ndi_has_video=ndi.has_video,
            ndi_source=ndi.selected_source,
            frame_width=ndi.frame_width,
            frame_height=ndi.frame_height,
            capture_fps=round(fps, 1) if fps else get_ai_runtime_status().capture_fps,
            model_loaded=self.detector.is_loaded,
            model_name=self.detector.model_name,
            detection_count=detections,
            inference_ms=round(inference_ms, 1),
        )

    def _poll_ndi_sources(self, *, user_refresh: bool) -> None:
        wait_s = 2.5 if user_refresh else 0.0
        sources = self.capture.refresh_ndi_sources(wait_s=wait_s)
        set_ndi_sources(sources)
        self._ndi_poll_at = time.time()

    def _ndi_setup_detail(self, ndi, source_count: int) -> str:
        if not ndi.is_available:
            return ndi.last_error or 'Install cyndilib + NDI Runtime on this PC'
        if source_count:
            return f'{source_count} NDI source(s) on LAN'
        return (
            'No NDI sources found — gaming PC OBS output on? '
            'Same network? NDI Runtime on BOTH PCs?'
        )

    def tick(self) -> None:
        config = self._get_config()
        if consume_ndi_refresh_request():
            self._ndi_refresh_pending = True
        now = time.time()
        if self._ndi_refresh_pending or (now - self._ndi_poll_at) >= 4.0:
            self._poll_ndi_sources(user_refresh=self._ndi_refresh_pending)
            self._ndi_refresh_pending = False

        armed = trigger_armed(config)
        ndi = self.capture.ndi
        image_size = int(config.get('ai_region_size', 640) or 640)
        source_count = len(get_ndi_sources())

        if not config.get('ai_enabled'):
            self._apply_capture_config(config)
            if not ndi.is_available:
                update_ai_runtime_status(
                    state='ndi_missing',
                    detail=self._ndi_setup_detail(ndi, source_count),
                    trigger_armed=False,
                    last_block_reason='',
                    in_zone_count=0,
                    ndi_connected=False,
                    ndi_has_video=False,
                    ndi_source=str(config.get('ai_ndi_source', '') or ''),
                    frame_width=0,
                    frame_height=0,
                    capture_fps=0.0,
                    model_loaded=False,
                    model_name='',
                    detection_count=0,
                    inference_ms=0.0,
                )
                time.sleep(0.2)
                return

            selected = str(config.get('ai_ndi_source', '') or '').strip()
            fps = 0.0
            if selected and ndi.has_video:
                if self.capture.grab_frame(image_size) is not None:
                    fps = self._update_fps()
            update_ai_runtime_status(
                state='preview' if selected else 'off',
                detail=self._ndi_setup_detail(ndi, source_count),
                trigger_armed=False,
                last_block_reason='',
                in_zone_count=0,
                ndi_connected=ndi.connected,
                ndi_has_video=ndi.has_video,
                ndi_source=ndi.selected_source or selected,
                frame_width=ndi.frame_width,
                frame_height=ndi.frame_height,
                capture_fps=round(fps, 1) if fps else get_ai_runtime_status().capture_fps,
                model_loaded=False,
                model_name='',
                detection_count=0,
                inference_ms=0.0,
            )
            time.sleep(0.02 if selected else 0.05)
            return

        self.start_detection_loop()
        self._apply_capture_config(config)

        if not ndi.is_available:
            self.trigger.evaluate(config, armed=armed, targets=[])
            self._publish(
                config,
                state='ndi_missing',
                detail=ndi.last_error or 'Install cyndilib + NDI Runtime',
                armed=armed,
                ndi=ndi,
            )
            time.sleep(0.2)
            return

        source = str(config.get('ai_ndi_source', '') or '').strip()
        if not source:
            self.trigger.evaluate(config, armed=armed, targets=[])
            self._publish(
                config,
                state='no_source',
                detail='Select NDI source from gaming PC',
                armed=armed,
                ndi=ndi,
            )
            time.sleep(0.05)
            return

        fps = 0.0
        if ndi.has_video:
            fps = self._update_fps()

        if not ndi.has_video:
            self.trigger.evaluate(config, armed=armed, targets=[])
            detail = ndi.last_error or (
                'No NDI video yet — OBS active scene on gaming PC? '
                'Try Preview source or allow NDI through Windows Firewall (Private).'
            )
            self._publish(config, state='waiting_frames', detail=detail, armed=armed, ndi=ndi)
            time.sleep(0.01)
            return

        if not self.detector.is_loaded and not self._ensure_model(config):
            self.trigger.evaluate(config, armed=armed, targets=[])
            err = self.detector.last_error or 'Set model path (.pt or .onnx)'
            self._publish(
                config,
                state='no_model',
                detail=err,
                armed=armed,
                ndi=ndi,
                fps=fps,
            )
            time.sleep(0.02)
            return

        targets, _frame_ctx, inference_ms, det_seq = self._get_latest_detection()
        aim_on = aim_armed(config)
        if config.get('ai_aim_enabled'):
            self.aim.step(armed=aim_on)
        if det_seq != self._last_trigger_seq:
            self._last_trigger_seq = det_seq
            self.trigger.evaluate(config, armed=armed, targets=targets)

        model_bit = self.detector.model_name or 'model'
        mode = str(config.get('ai_assist_mode', 'trigger') or 'trigger')
        pred_ms = int(config.get('ai_trigger_prediction_ms', 35) or 0)
        extra = ''
        if mode in {'trigger', 'both'} and pred_ms > 0:
            extra += f' · lead {pred_ms}ms'
        if mode in {'aim', 'both'}:
            extra += f' · aim:{self.aim.last_block_reason or "ok"}'
        self._publish(
            config,
            state='running',
            detail=f'{len(targets)} target(s) · {model_bit} · {inference_ms:.0f}ms infer{extra}',
            armed=armed,
            ndi=ndi,
            fps=fps,
            detections=len(targets),
            inference_ms=inference_ms,
        )
        time.sleep(0.001)
