"""Global settings — legacy first tab."""

from __future__ import annotations

from app.gui.qt import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)

from app.core.config import load_config, save_config
from app.gui.theme import ACCENT_BLUE
from app.gui.widgets import (
    Divider,
    SettingRow,
    Switch,
    WarningBanner,
    settings_card,
)
from app.recoil.engine import invalidate_config_cache


class GlobalPanel(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._building = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 12)

        card, body = settings_card(
            'Global Control',
            'Master switch, input method, and shared options.',
            badge='⚙',
        )

        key_row = QWidget()
        key_layout = QHBoxLayout(key_row)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(8)
        self._keybind = QComboBox()
        self._keybind.addItems(['M4', 'M5'])
        self._keybind.currentTextChanged.connect(self._on_keybind)
        self._enabled = Switch(accent='blue')
        self._enabled.stateChanged.connect(self._on_enabled)
        key_layout.addWidget(self._keybind)
        key_layout.addWidget(self._enabled)
        body.addWidget(SettingRow(
            'Global recoil',
            subtitle='Master switch and toggle hotkey.',
            control=key_row,
        ))
        body.addWidget(Divider())

        self._require_rmb = Switch(accent='blue')
        self._require_rmb.stateChanged.connect(self._on_require_rmb)
        body.addWidget(SettingRow(
            'Require RMB',
            subtitle='Recoil only when right mouse is held.',
            control=self._require_rmb,
        ))

        self._shutdown = Switch(accent='amber')
        self._shutdown.stateChanged.connect(self._on_shutdown)
        body.addWidget(SettingRow(
            'Shutdown PC on Stop',
            subtitle='Shut down Windows when closing KryptAim.',
            control=self._shutdown,
        ))

        self._input_method = QComboBox()
        self._input_method.addItem('Hardware (Makcu)', 'makcu')
        self._input_method.setEnabled(False)
        body.addWidget(SettingRow(
            'Input method',
            subtitle='Dual-PC rebuild uses Makcu on KryptAim PC.',
            control=self._input_method,
        ))

        self._username = QLineEdit()
        self._username.setPlaceholderText('Anonymous')
        self._username.editingFinished.connect(self._on_username)
        body.addWidget(SettingRow(
            'Cloud username',
            subtitle='Author name when sharing patterns.',
            control=self._username,
        ))

        access_row = QWidget()
        access_layout = QVBoxLayout(access_row)
        access_layout.setContentsMargins(0, 0, 0, 0)
        access_lbl = QLabel('FREE ACCESS ENABLED')
        access_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        access_lbl.setStyleSheet(
            f'color: {ACCENT_BLUE}; font-size: 10px; font-weight: 700; '
            'letter-spacing: 0.14em; background: transparent;'
        )
        access_layout.addWidget(access_lbl)
        body.addWidget(SettingRow(
            'Access mode',
            subtitle='All features unlocked.',
            control=access_row,
        ))

        self._warning = WarningBanner(
            'Dual-PC: Makcu moves the gaming PC mouse. Dev mode uses local mouse only.'
        )
        body.addWidget(self._warning)

        root.addWidget(card)
        self.reload_from_disk()

    def reload_from_disk(self) -> None:
        self._building = True
        config = load_config()
        self._enabled.setChecked(bool(config.get('recoil_enabled')))
        self._require_rmb.setChecked(bool(config.get('recoil_require_rmb')))
        self._shutdown.setChecked(bool(config.get('shutdown_on_app_stop')))
        self._username.setText(str(config.get('cloud_username', 'Anonymous') or 'Anonymous'))
        kb = config.get('recoil_keybind', 'M4')
        ki = self._keybind.findText(kb)
        if ki >= 0:
            self._keybind.setCurrentIndex(ki)
        self._building = False

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

    def _on_enabled(self, state: int) -> None:
        self._persist(recoil_enabled=self._is_checked(state))

    def _on_require_rmb(self, state: int) -> None:
        self._persist(recoil_require_rmb=self._is_checked(state))

    def _on_shutdown(self, state: int) -> None:
        self._persist(shutdown_on_app_stop=self._is_checked(state))

    def _on_keybind(self, text: str) -> None:
        self._persist(recoil_keybind=text)

    def _on_username(self) -> None:
        name = self._username.text().strip() or 'Anonymous'
        self._persist(cloud_username=name)

    def set_dev_warning(self, dev_mode: bool) -> None:
        if dev_mode:
            self._warning.setText(
                'DEV MODE — local mouse only. For dual-PC use run.bat without --dev.'
            )
        else:
            self._warning.setText(
                'Dual-PC: Makcu moves the gaming PC mouse via KryptAim hardware path.'
            )
