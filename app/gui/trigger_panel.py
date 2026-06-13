"""Trigger bot settings."""

from __future__ import annotations

from app.gui.qt import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)

from app.ai.lifecycle import invalidate_config_cache
from app.ai.status import get_ai_runtime_status
from app.core.config import load_config, save_config
from app.gui.theme import ACCENT_AMBER, make_group, section_title, setup_form
from app.gui.widgets import add_checkbox_row, add_slider_row, hint_label, status_label


class TriggerPanel(QWidget):
    changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        compact: bool = False,
        show_model: bool = True,
    ) -> None:
        super().__init__(parent)
        self._building = False

        root = QVBoxLayout(self)
        margins = (0, 0, 0, 0) if compact else (12, 12, 12, 12)
        root.setContentsMargins(*margins)
        root.setSpacing(10 if compact else 16)

        if show_model:
            if compact:
                model_heading = QLabel('Model')
                model_heading.setStyleSheet(section_title('Model', color=ACCENT_AMBER))
                root.addWidget(model_heading)

            model_box = make_group('YOLO model' if not compact else '')
            model_form = QFormLayout(model_box)
            setup_form(model_form)

            path_row = QHBoxLayout()
            path_row.setSpacing(8)
            self._model_path = QLineEdit()
            self._model_path.setPlaceholderText('Path to .pt or .onnx')
            self._model_path.editingFinished.connect(self._on_model_path)
            browse = QPushButton('Browse')
            browse.setFixedWidth(80)
            browse.clicked.connect(self._on_browse_model)
            path_row.addWidget(self._model_path, 1)
            path_row.addWidget(browse)
            path_wrap = QWidget()
            path_wrap.setLayout(path_row)
            model_form.addRow('Model file', path_wrap)

            self._detect_conf = add_slider_row(
                model_form,
                'Detection conf %',
                low=10,
                high=90,
                on_change=self._on_detect_conf,
            )
            self._player_class = QLineEdit()
            self._player_class.setPlaceholderText('CS2: CT or T (enemy team). Empty = both')
            self._player_class.editingFinished.connect(self._on_player_class)
            model_form.addRow('Player class', self._player_class)

            self._head_class = QLineEdit()
            self._head_class.setPlaceholderText('Auto if model has head. CS2_640 = CT/T only')
            self._head_class.editingFinished.connect(self._on_head_class)
            model_form.addRow('Head class', self._head_class)

            root.addWidget(model_box)
        else:
            self._model_path = QLineEdit()
            self._detect_conf = None  # type: ignore[assignment]
            self._player_class = QLineEdit()
            self._head_class = QLineEdit()

        self._compact = compact

        if compact:
            combat_heading = QLabel('Combat assist')
            combat_heading.setStyleSheet(section_title('Combat assist', color=ACCENT_AMBER))
            root.addWidget(combat_heading)

        group = make_group('Combat assist' if not compact else '')
        form = QFormLayout(group)
        setup_form(form)

        self._ai_enabled = QCheckBox('AI enabled')
        self._ai_enabled.stateChanged.connect(self._on_ai_enabled)
        if not compact:
            add_checkbox_row(form, self._ai_enabled)

        self._assist_mode = QComboBox()
        self._assist_mode.addItem('Trigger + prediction', 'trigger')
        self._assist_mode.addItem('Aim only', 'aim')
        self._assist_mode.addItem('Aim + trigger', 'both')
        self._assist_mode.currentIndexChanged.connect(self._on_assist_mode)
        form.addRow('Mode', self._assist_mode)

        self._always_on = QCheckBox('Always on (no hold key)')
        self._always_on.stateChanged.connect(self._on_always_on)
        add_checkbox_row(form, self._always_on)

        self._keybind = QComboBox()
        self._keybind.addItem('Hold M4', 'M4')
        self._keybind.addItem('Hold M5', 'M5')
        self._keybind.addItem('None', 'None')
        self._keybind.currentIndexChanged.connect(self._on_keybind)
        form.addRow('Arm key', self._keybind)

        self._radius = add_slider_row(
            form, 'Radius (px)', low=4, high=24, on_change=self._on_radius,
        )
        self._delay = add_slider_row(
            form, 'Delay (ms)', low=0, high=120, on_change=self._on_delay,
        )
        self._cooldown = add_slider_row(
            form, 'Cooldown (ms)', low=50, high=800, on_change=self._on_cooldown,
        )
        self._min_conf = add_slider_row(
            form, 'Min confidence %', low=20, high=90, on_change=self._on_min_conf,
        )
        self._prediction = add_slider_row(
            form, 'Lead / prediction (ms)', low=0, high=80, on_change=self._on_prediction,
        )
        self._aim_point = QComboBox()
        self._aim_point.addItem('Head', 'head')
        self._aim_point.addItem('Body', 'body')
        self._aim_point.addItem('Neck', 'neck')
        self._aim_point.addItem('BBox center', 'center')
        self._aim_point.currentIndexChanged.connect(self._on_aim_point)
        form.addRow('Aim point', self._aim_point)

        self._aim_speed = add_slider_row(
            form, 'Aim speed %', low=25, high=200, on_change=self._on_aim_speed,
        )
        self._aim_fov = add_slider_row(
            form, 'Aim FOV (crop px)', low=40, high=400, on_change=self._on_aim_fov,
        )
        self._spray_block = QCheckBox('Block while recoil enabled (rifles / SMGs)')
        self._spray_block.setChecked(True)
        self._spray_block.stateChanged.connect(self._on_spray_block)
        add_checkbox_row(form, self._spray_block)
        hint = hint_label(
            'Pistols / snipers: Trigger or Aim. Recoil tab = spray rifles & SMGs. '
            'ONNX GPU: pip install onnxruntime-gpu in .venv'
        )
        form.addRow('', hint)

        self._status = status_label('Off')
        form.addRow('Status', self._status)

        root.addWidget(group)
        root.addStretch()

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start()

        self.reload_from_disk()
        self._refresh_status()

    def _refresh_status(self) -> None:
        status = get_ai_runtime_status()
        armed = 'Armed' if status.trigger_armed else 'Not armed'
        ndi = 'NDI OK' if status.ndi_has_video else ('NDI link' if status.ndi_connected else 'NDI --')
        reason = status.last_block_reason or '--'
        model = status.model_name if status.model_loaded else 'not loaded'
        self._status.setText(
            f'{status.state}  |  {armed}  |  {ndi}  |  {model}\n'
            f'{status.detail}\n'
            f'Dets: {status.detection_count}  |  Infer: {status.inference_ms:.0f}ms  |  '
            f'Block: {reason}  |  In zone: {status.in_zone_count}  |  '
            f'Aim: {status.aim_block_reason or "--"}'
        )

    def reload_from_disk(self) -> None:
        self._building = True
        config = load_config()
        self._ai_enabled.setChecked(bool(config.get('ai_enabled')))
        mode = str(config.get('ai_assist_mode', 'trigger') or 'trigger')
        mi = self._assist_mode.findData(mode)
        if mi >= 0:
            self._assist_mode.setCurrentIndex(mi)
        self._always_on.setChecked(bool(config.get('ai_trigger_always_on')))
        key = (config.get('ai_trigger_keybind') or 'M4').strip()
        ki = self._keybind.findData(key)
        if ki >= 0:
            self._keybind.setCurrentIndex(ki)
        self._radius.setValue(int(config.get('ai_trigger_radius_px', 8)))
        self._delay.setValue(int(config.get('ai_trigger_delay_ms', 30)))
        self._cooldown.setValue(int(config.get('ai_trigger_cooldown_ms', 120)))
        conf_pct = int(round(float(config.get('ai_trigger_min_conf', 0.35)) * 100))
        self._min_conf.setValue(conf_pct)
        self._model_path.setText(str(config.get('ai_model_path', '') or ''))
        if self._detect_conf is not None:
            det_pct = int(round(float(config.get('ai_detection_conf', 0.25)) * 100))
            self._detect_conf.setValue(det_pct)
        self._player_class.setText(str(config.get('ai_player_class', '') or ''))
        self._head_class.setText(str(config.get('ai_head_class', '') or ''))
        ap = str(config.get('ai_aim_point', 'head') or 'head')
        if ap == 'chest':
            ap = 'head'
        api = self._aim_point.findData(ap)
        if api >= 0:
            self._aim_point.setCurrentIndex(api)
        self._prediction.setValue(int(config.get('ai_trigger_prediction_ms', 35)))
        self._aim_speed.setValue(int(round(float(config.get('ai_aim_speed', 1.0)) * 100)))
        self._aim_fov.setValue(int(config.get('ai_aim_max_px', 280)))
        self._spray_block.setChecked(bool(config.get('ai_trigger_spray_block', True)))
        self._building = False
        self._sync_mode_widgets()

    def _persist(self, **updates) -> None:
        if self._building:
            return
        config = load_config()
        config.update(updates)
        save_config(config)
        invalidate_config_cache()
        self.changed.emit()

    @staticmethod
    def _is_checked(state: int) -> bool:
        return state == Qt.CheckState.Checked.value

    def _on_ai_enabled(self, state: int) -> None:
        self._persist(ai_enabled=self._is_checked(state))

    def _sync_mode_widgets(self) -> None:
        mode = self._assist_mode.currentData() or 'trigger'
        trigger_on = mode in {'trigger', 'both'}
        aim_on = mode in {'aim', 'both'}
        for w in (self._radius, self._delay, self._cooldown, self._prediction):
            w.setEnabled(trigger_on)
        for w in (self._aim_point, self._aim_speed, self._aim_fov):
            w.setEnabled(aim_on)

    def _on_assist_mode(self, _index: int) -> None:
        mode = self._assist_mode.currentData() or 'trigger'
        updates: dict = {'ai_assist_mode': mode}
        if mode == 'aim':
            updates['ai_trigger_prediction_ms'] = 0
        self._persist(**updates)
        self._sync_mode_widgets()

    def _on_always_on(self, state: int) -> None:
        on = self._is_checked(state)
        self._persist(ai_trigger_always_on=on, ai_aim_always_on=on)

    def _on_keybind(self, _index: int) -> None:
        self._persist(ai_trigger_keybind=self._keybind.currentData())

    def _on_radius(self, value: int) -> None:
        self._persist(ai_trigger_radius_px=value)

    def _on_delay(self, value: int) -> None:
        self._persist(ai_trigger_delay_ms=value)

    def _on_cooldown(self, value: int) -> None:
        self._persist(ai_trigger_cooldown_ms=value)

    def _on_min_conf(self, value: int) -> None:
        self._persist(ai_trigger_min_conf=round(value / 100.0, 2))

    def _on_model_path(self) -> None:
        self._persist(ai_model_path=self._model_path.text().strip())

    def _on_browse_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Select YOLO model',
            self._model_path.text().strip() or '',
            'YOLO models (*.pt *.onnx);;All files (*.*)',
        )
        if path:
            self._model_path.setText(path)
            self._persist(ai_model_path=path)

    def _on_detect_conf(self, value: int) -> None:
        self._persist(ai_detection_conf=round(value / 100.0, 2))

    def _on_player_class(self) -> None:
        self._persist(ai_player_class=self._player_class.text().strip())

    def _on_head_class(self) -> None:
        self._persist(ai_head_class=self._head_class.text().strip())

    def _on_aim_point(self, _index: int) -> None:
        self._persist(ai_aim_point=self._aim_point.currentData() or 'head')

    def _on_prediction(self, value: int) -> None:
        self._persist(ai_trigger_prediction_ms=value)

    def _on_spray_block(self, state: int) -> None:
        self._persist(ai_trigger_spray_block=self._is_checked(state))

    def _on_aim_speed(self, value: int) -> None:
        self._persist(ai_aim_speed=round(value / 100.0, 2))

    def _on_aim_fov(self, value: int) -> None:
        self._persist(ai_aim_max_px=value)
