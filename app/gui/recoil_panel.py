"""CS2 recoil — legacy single-card layout."""

from __future__ import annotations

from app.gui.qt import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)

from app.core.config import load_config, save_config
from app.gui.theme import setup_form
from app.gui.widgets import (
    Divider,
    SettingRow,
    Switch,
    add_slider_row,
    settings_card,
)
from app.recoil.engine import invalidate_config_cache
from app.recoil.weapon_data import WeaponData


class RecoilPanel(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None, *, compact: bool = False) -> None:
        super().__init__(parent)
        self._building = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 12)
        root.setSpacing(0)

        card, body = settings_card(
            'Game Engine',
            'CS2 spray rifles & SMGs — pistols/snipers on KryptAim AI tab.',
        )

        self._category = QComboBox()
        for category_id, label in WeaponData.CATEGORY_LABELS.items():
            self._category.addItem(label, category_id)
        self._category.currentIndexChanged.connect(self._on_category)
        body.addWidget(SettingRow('Weapon type', subtitle='Rifles or SMGs.', control=self._category))

        self._weapon = QComboBox()
        self._weapon.currentIndexChanged.connect(self._on_weapon)
        body.addWidget(SettingRow(
            'Weapon',
            subtitle='Active spray profile.',
            control=self._weapon,
        ))

        self._sensitivity = QDoubleSpinBox()
        self._sensitivity.setRange(0.1, 10.0)
        self._sensitivity.setSingleStep(0.05)
        self._sensitivity.setDecimals(2)
        self._sensitivity.valueChanged.connect(self._on_sensitivity)
        body.addWidget(SettingRow(
            'In-game sensitivity',
            subtitle='Must match CS2 settings.',
            control=self._sensitivity,
        ))

        body.addWidget(Divider())

        self._return_crosshair = Switch()
        self._return_crosshair.stateChanged.connect(self._on_return_crosshair)
        body.addWidget(SettingRow(
            'Return crosshair',
            subtitle='Reset view when you release fire.',
            control=self._return_crosshair,
        ))

        body.addWidget(Divider())

        tune_heading = QLabel('Fine tune')
        tune_heading.setStyleSheet(
            'color: rgba(255,255,255,0.55); font-size: 11px; font-weight: 700; '
            'letter-spacing: 0.1em; text-transform: uppercase; padding-top: 4px;'
        )
        body.addWidget(tune_heading)

        self._random = Switch()
        self._random.stateChanged.connect(self._on_random)
        body.addWidget(SettingRow(
            'Randomisation',
            subtitle='Humanize spray steps.',
            control=self._random,
        ))

        self._random_strength = QDoubleSpinBox()
        self._random_strength.setRange(0.0, 20.0)
        self._random_strength.setSingleStep(0.5)
        self._random_strength.valueChanged.connect(self._on_random_strength)
        body.addWidget(SettingRow(
            'Random strength',
            control=self._random_strength,
        ))

        sliders = QWidget()
        slider_form = QFormLayout(sliders)
        setup_form(slider_form)
        self._x_control = add_slider_row(
            slider_form, 'X control %', low=0, high=100, on_change=self._on_x_control,
        )
        self._y_control = add_slider_row(
            slider_form, 'Y control %', low=0, high=100, on_change=self._on_y_control,
        )
        body.addWidget(sliders)

        root.addWidget(card)

        self.reload_from_disk()

    def reload_from_disk(self) -> None:
        self._building = True
        config = load_config()
        weapon = config.get('recoil_cs2_settings', {}).get('cs2_weapon', 'assault_rifle')
        self._select_weapon(weapon)
        self._sensitivity.setValue(
            float(config.get('recoil_cs2_settings', {}).get('cs2_sensitivity', 1.25))
        )
        self._return_crosshair.setChecked(bool(config.get('recoil_return_crosshair')))
        self._random.setChecked(bool(config.get('recoil_randomisation')))
        self._random_strength.setValue(float(config.get('recoil_random_strength', 5.0)))
        self._x_control.setValue(int(config.get('recoil_x_control', 100)))
        self._y_control.setValue(int(config.get('recoil_y_control', 100)))
        self._building = False

    def _persist(self, **updates) -> None:
        if self._building:
            return
        config = load_config()
        for key, value in updates.items():
            if key in ('cs2_weapon', 'cs2_sensitivity'):
                config.setdefault('recoil_cs2_settings', {})[key] = value
            else:
                config[key] = value
        config['recoil_mode'] = 'CS2'
        save_config(config)
        invalidate_config_cache()
        self.changed.emit()

    @staticmethod
    def _is_checked(state: int) -> bool:
        return state == Qt.CheckState.Checked.value

    def _populate_weapons(self, category_id: str, select_weapon: str | None = None) -> None:
        labels = WeaponData.weapon_labels()
        self._weapon.blockSignals(True)
        self._weapon.clear()
        for weapon_id in WeaponData.weapons_in_category(category_id):
            self._weapon.addItem(labels[weapon_id], weapon_id)
        if select_weapon:
            idx = self._weapon.findData(select_weapon)
            if idx >= 0:
                self._weapon.setCurrentIndex(idx)
        elif self._weapon.count():
            self._weapon.setCurrentIndex(0)
        self._weapon.blockSignals(False)

    def _select_weapon(self, weapon_id: str) -> None:
        category_id = WeaponData.category_for_weapon(weapon_id)
        cat_idx = self._category.findData(category_id)
        if cat_idx >= 0:
            self._category.blockSignals(True)
            self._category.setCurrentIndex(cat_idx)
            self._category.blockSignals(False)
        self._populate_weapons(category_id, weapon_id)

    def _on_return_crosshair(self, state: int) -> None:
        self._persist(recoil_return_crosshair=self._is_checked(state))

    def _on_category(self, _index: int) -> None:
        if self._building:
            return
        category_id = self._category.currentData()
        previous = self._weapon.currentData()
        self._populate_weapons(category_id)
        if previous and self._weapon.findData(previous) >= 0:
            self._weapon.setCurrentIndex(self._weapon.findData(previous))
        self._persist(cs2_weapon=self._weapon.currentData())

    def _on_weapon(self, _index: int) -> None:
        weapon_id = self._weapon.currentData()
        if weapon_id:
            self._persist(cs2_weapon=weapon_id)

    def _on_sensitivity(self, value: float) -> None:
        self._persist(cs2_sensitivity=value)

    def _on_random(self, state: int) -> None:
        self._persist(recoil_randomisation=self._is_checked(state))

    def _on_random_strength(self, value: float) -> None:
        self._persist(recoil_random_strength=value)

    def _on_x_control(self, value: int) -> None:
        self._persist(recoil_x_control=value)

    def _on_y_control(self, value: int) -> None:
        self._persist(recoil_y_control=value)
