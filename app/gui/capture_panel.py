"""NDI capture settings."""

from __future__ import annotations

from app.gui.qt import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTimer,
    Signal,
    QVBoxLayout,
    QWidget,
)

from app.ai.ndi_control import get_ndi_sources, request_ndi_refresh
from app.ai.status import get_ai_runtime_status
from app.core.config import load_config, save_config
from app.gui.theme import make_group, section_title, setup_form
from app.gui.widgets import hint_label, status_label


class CapturePanel(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None, *, compact: bool = False) -> None:
        super().__init__(parent)
        self._building = False
        self._known_sources: list[str] = []

        root = QVBoxLayout(self)
        margins = (0, 0, 0, 0) if compact else (12, 12, 12, 12)
        root.setContentsMargins(*margins)
        root.setSpacing(10 if compact else 16)

        if compact:
            heading = QLabel('Capture')
            heading.setStyleSheet(section_title('Capture'))
            root.addWidget(heading)

        group = make_group('NDI stream' if not compact else '')
        form = QFormLayout(group)
        setup_form(form)

        res_row = QHBoxLayout()
        res_row.setSpacing(10)
        self._width = QSpinBox()
        self._width.setRange(640, 3840)
        self._width.setSingleStep(10)
        self._width.valueChanged.connect(self._on_resolution)
        self._height = QSpinBox()
        self._height.setRange(480, 2160)
        self._height.setSingleStep(10)
        self._height.valueChanged.connect(self._on_resolution)
        w_lbl = QLabel('W')
        h_lbl = QLabel('H')
        w_lbl.setFixedWidth(16)
        h_lbl.setFixedWidth(16)
        res_row.addWidget(w_lbl)
        res_row.addWidget(self._width, 1)
        res_row.addWidget(h_lbl)
        res_row.addWidget(self._height, 1)
        res_wrap = QWidget()
        res_wrap.setLayout(res_row)
        form.addRow('Gaming PC', res_wrap)

        self._region = QSpinBox()
        self._region.setRange(160, 1280)
        self._region.setSingleStep(32)
        self._region.valueChanged.connect(self._on_region)
        form.addRow('Crop size', self._region)

        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        self._source = QComboBox()
        self._source.currentIndexChanged.connect(self._on_source)
        self._refresh = QPushButton('Refresh')
        self._refresh.setFixedWidth(90)
        self._refresh.clicked.connect(self._on_refresh)
        source_row.addWidget(self._source, 1)
        source_row.addWidget(self._refresh)
        source_wrap = QWidget()
        source_wrap.setLayout(source_row)
        form.addRow('NDI source', source_wrap)

        self._ndi_status = status_label('Waiting...')
        form.addRow('Status', self._ndi_status)

        hint = hint_label('Gaming PC: OBS NDI output. Both PCs need NDI Runtime.')
        form.addRow('', hint)

        root.addWidget(group)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll_sources_and_status)
        self._timer.start()

        self.reload_from_disk()

    def reload_from_disk(self) -> None:
        self._building = True
        config = load_config()
        self._width.setValue(int(config.get('ai_main_pc_width', 1920)))
        self._height.setValue(int(config.get('ai_main_pc_height', 1080)))
        self._region.setValue(int(config.get('ai_region_size', 640)))
        self._sync_source_combo(str(config.get('ai_ndi_source', '') or ''))
        self._building = False
        request_ndi_refresh()

    def _sync_source_combo(self, selected: str) -> None:
        self._source.blockSignals(True)
        self._source.clear()
        self._source.addItem('Select source...', '')
        for name in self._known_sources:
            self._source.addItem(name, name)
        if selected:
            idx = self._source.findData(selected)
            if idx < 0:
                self._source.addItem(selected, selected)
                idx = self._source.findData(selected)
            if idx >= 0:
                self._source.setCurrentIndex(idx)
        self._source.blockSignals(False)

    def _poll_sources_and_status(self) -> None:
        sources = get_ndi_sources()
        if sources != self._known_sources:
            self._known_sources = sources
            selected = self._source.currentData() or ''
            self._sync_source_combo(str(selected))

        status = get_ai_runtime_status()
        conn = (
            'Video OK'
            if status.ndi_has_video
            else ('Linked' if status.ndi_connected else 'Not connected')
        )
        fps = f'{status.capture_fps:.1f} fps' if status.capture_fps else '-- fps'
        dims = (
            f'{status.frame_width}x{status.frame_height}'
            if status.frame_width and status.frame_height
            else '--'
        )
        ndi_states = {'ndi_missing', 'no_source', 'waiting_frames', 'off', 'preview'}
        extra = status.detail if status.state in ndi_states else ''
        if not sources and status.state in {'off', 'preview', 'ndi_missing'}:
            extra = extra or 'Click Refresh — wait ~3s for LAN discovery'
        line2 = f'\n{extra}' if extra else ''
        src_count = f'{len(sources)} on LAN' if sources else '0 on LAN'
        self._ndi_status.setText(
            f'{conn}  |  {status.ndi_source or "no source"}  |  {dims}  |  {fps}  |  {src_count}{line2}'
        )

    def _persist(self, **updates) -> None:
        if self._building:
            return
        config = load_config()
        config.update(updates)
        save_config(config)
        self.changed.emit()

    def _on_resolution(self) -> None:
        self._persist(
            ai_main_pc_width=self._width.value(),
            ai_main_pc_height=self._height.value(),
        )

    def _on_region(self, value: int) -> None:
        self._persist(ai_region_size=value)

    def _on_source(self, _index: int) -> None:
        if self._building:
            return
        self._persist(ai_ndi_source=self._source.currentData() or '')

    def _on_refresh(self) -> None:
        request_ndi_refresh()
