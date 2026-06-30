"""AimSync AI tab — legacy-style header, stats, quick setup, capture + trigger."""

from __future__ import annotations

from app.gui.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)

from app.ai.lifecycle import invalidate_config_cache
from app.ai.ndi_control import request_ndi_refresh
from app.ai.presets import apply_quickstart
from app.ai.status import get_ai_runtime_status
from app.core.config import load_config, save_config
from app.gui.capture_panel import CapturePanel
from app.gui.theme import (
    ACCENT_AMBER,
    make_amber_card,
    card_layout,
    hint_style,
    style_danger_button,
    style_primary_button,
    style_secondary_button,
)
from app.gui.trigger_panel import TriggerPanel
from app.gui.widgets import StatCard, hint_label


class AiPanel(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        header_card = make_amber_card()
        header_layout = card_layout(header_card, margins=(20, 18, 20, 18))
        header_row = QHBoxLayout()
        header_row.setSpacing(16)
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel('AimSync AI')
        title.setStyleSheet(
            'font-size: 18px; font-weight: 700; color: #fafafa; background: transparent;'
        )
        subtitle = QLabel(
            'NDI capture → YOLO detection → Makcu aim & trigger. Use Quick setup first.'
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(hint_style())
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col, 1)

        self._toggle_btn = QPushButton('Start AI')
        self._toggle_btn.setFixedWidth(120)
        self._toggle_btn.clicked.connect(self._on_toggle_ai)
        header_row.addWidget(self._toggle_btn, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(header_row)
        root.addWidget(header_card)

        stats_row = QGridLayout()
        stats_row.setSpacing(8)
        self._stat_engine = StatCard('Engine')
        self._stat_model = StatCard('Model')
        self._stat_ndi = StatCard('NDI')
        self._stat_infer = StatCard('Inference')
        stats_row.addWidget(self._stat_engine, 0, 0)
        stats_row.addWidget(self._stat_model, 0, 1)
        stats_row.addWidget(self._stat_ndi, 1, 0)
        stats_row.addWidget(self._stat_infer, 1, 1)
        root.addLayout(stats_row)

        readiness = make_amber_card()
        ready_layout = card_layout(readiness, margins=(16, 14, 16, 14))
        ready_row = QHBoxLayout()
        ready_row.setSpacing(12)
        ready_text = QVBoxLayout()
        ready_title = QLabel('Ready to play')
        ready_title.setStyleSheet(
            f'color: {ACCENT_AMBER}; font-size: 14px; font-weight: 600; background: transparent;'
        )
        self._ready_hint = QLabel('Complete NDI + model below, then Quick setup.')
        self._ready_hint.setWordWrap(True)
        self._ready_hint.setStyleSheet(hint_style())
        ready_text.addWidget(ready_title)
        ready_text.addWidget(self._ready_hint)
        ready_row.addLayout(ready_text, 1)

        btn_col = QHBoxLayout()
        btn_col.setSpacing(8)
        self._quick_btn = QPushButton('Quick setup')
        style_primary_button(self._quick_btn)
        self._quick_btn.clicked.connect(lambda: self._run_quickstart(trigger_only=False))
        self._trigger_quick_btn = QPushButton('Trigger setup')
        style_secondary_button(self._trigger_quick_btn)
        self._trigger_quick_btn.clicked.connect(lambda: self._run_quickstart(trigger_only=True))
        btn_col.addWidget(self._quick_btn)
        btn_col.addWidget(self._trigger_quick_btn)
        ready_row.addLayout(btn_col)
        ready_layout.addLayout(ready_row)
        root.addWidget(readiness)

        self._capture_panel = CapturePanel(compact=True)
        self._trigger_panel = TriggerPanel(compact=True, show_model=True)
        root.addWidget(self._capture_panel)
        root.addWidget(self._trigger_panel)
        root.addStretch()

        self._capture_panel.changed.connect(self.changed.emit)
        self._trigger_panel.changed.connect(self.changed.emit)

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start()

        self.reload_from_disk()
        self._refresh_stats()

    def reload_from_disk(self) -> None:
        config = load_config()
        self._sync_toggle_button(bool(config.get('ai_enabled')))
        self._capture_panel.reload_from_disk()
        self._trigger_panel.reload_from_disk()

    def _sync_toggle_button(self, enabled: bool) -> None:
        if enabled:
            self._toggle_btn.setText('Stop AI')
            style_danger_button(self._toggle_btn)
        else:
            self._toggle_btn.setText('Start AI')
            style_primary_button(self._toggle_btn)

    def _on_toggle_ai(self) -> None:
        config = load_config()
        enabled = not bool(config.get('ai_enabled'))
        config['ai_enabled'] = enabled
        save_config(config)
        invalidate_config_cache()
        self._sync_toggle_button(enabled)
        self._trigger_panel.reload_from_disk()
        self.changed.emit()

    def _run_quickstart(self, *, trigger_only: bool) -> None:
        config = load_config()
        config.update(apply_quickstart(trigger_only=trigger_only))
        save_config(config)
        invalidate_config_cache()
        request_ndi_refresh()
        self.reload_from_disk()
        if trigger_only:
            self._ready_hint.setText('Trigger mode — lowest latency path. Hold M4 or use Always on.')
        else:
            self._ready_hint.setText('Quick setup applied — verify NDI source and model path.')
        self.changed.emit()

    def _refresh_stats(self) -> None:
        config = load_config()
        status = get_ai_runtime_status()
        self._sync_toggle_button(bool(config.get('ai_enabled')))

        armed = 'Armed' if status.trigger_armed else 'Idle'
        fps = f'{status.capture_fps:.0f} fps' if status.capture_fps else '— fps'
        self._stat_engine.set_values(
            status.state.replace('_', ' ').title(),
            f'{armed}  ·  {fps}',
        )

        model = status.model_name if status.model_loaded else 'Not loaded'
        mode = str(config.get('ai_assist_mode', 'trigger') or 'trigger')
        self._stat_model.set_values(model, f'Mode: {mode}')

        ndi = (
            'Video OK'
            if status.ndi_has_video
            else ('Linked' if status.ndi_connected else 'Offline')
        )
        src = status.ndi_source or 'No source'
        dims = (
            f'{status.frame_width}×{status.frame_height}'
            if status.frame_width and status.frame_height
            else '—'
        )
        self._stat_ndi.set_values(ndi, f'{src}  ·  {dims}')

        infer = f'{status.inference_ms:.0f} ms' if status.inference_ms else '—'
        dets = str(status.detection_count)
        block = status.last_block_reason or status.aim_block_reason or '—'
        self._stat_infer.set_values(infer, f'Dets: {dets}  ·  Block: {block}')
