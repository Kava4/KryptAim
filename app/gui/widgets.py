"""Legacy-style setting rows, toggles, panel chrome."""

from __future__ import annotations

from app.gui.qt import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)
from app.gui.theme import (
    ACCENT_AMBER_DARK,
    BG_MUTED,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    hint_style,
    make_card,
    card_layout,
)


def add_checkbox_row(form: QFormLayout, checkbox) -> None:
    form.addRow('', checkbox)


def add_slider_row(
    form: QFormLayout,
    label: str,
    *,
    low: int,
    high: int,
    on_change,
    initial: int | None = None,
) -> QSlider:
    row = QHBoxLayout()
    row.setSpacing(10)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(low, high)
    slider.setMinimumWidth(120)
    slider.valueChanged.connect(on_change)
    value_lbl = QLabel(str(initial if initial is not None else low))
    value_lbl.setMinimumWidth(40)
    value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    value_lbl.setStyleSheet(
        f'color: {ACCENT_AMBER_DARK}; font-weight: 700; font-size: 12px; background: transparent;'
    )
    slider.valueChanged.connect(lambda v, lbl=value_lbl: lbl.setText(str(v)))
    row.addWidget(slider, 1)
    row.addWidget(value_lbl)
    wrap = QWidget()
    wrap.setLayout(row)
    form.addRow(label, wrap)
    if initial is not None:
        slider.setValue(initial)
    slider._value_label = value_lbl  # type: ignore[attr-defined]
    return slider


def status_label(text: str = '') -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setMinimumHeight(44)
    lbl.setStyleSheet(
        f'color: {TEXT_MUTED}; font-size: 12px; background: {BG_MUTED}; '
        'border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 12px;'
    )
    return lbl


def hint_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(hint_style())
    return lbl


class Divider(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet('background: rgba(255,255,255,0.08); border: none;')


class Switch(QCheckBox):
    """Pill toggle — legacy web switch feel."""

    def __init__(self, parent: QWidget | None = None, *, accent: str = 'amber') -> None:
        super().__init__(parent)
        self.setProperty('switch', True)
        self.setProperty('switchAccent', accent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class StatusBadge(QLabel):
    def __init__(
        self,
        text: str,
        *,
        tone: str = 'ok',
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setProperty('badgeTone', tone)
        self.setStyleSheet(self._style(tone))

    @staticmethod
    def _style(tone: str) -> str:
        tones = {
            'ok': ('rgba(34,197,94,0.12)', 'rgba(34,197,94,0.35)', '#86efac'),
            'warn': ('rgba(251,191,36,0.12)', 'rgba(251,191,36,0.35)', '#fcd34d'),
            'bad': ('rgba(239,68,68,0.12)', 'rgba(248,113,113,0.35)', '#fca5a5'),
            'info': ('rgba(59,130,246,0.12)', 'rgba(59,130,246,0.35)', '#93c5fd'),
        }
        bg, border, fg = tones.get(tone, tones['info'])
        return (
            f'background: {bg}; border: 1px solid {border}; color: {fg}; '
            'font-size: 10px; font-weight: 700; letter-spacing: 0.08em; '
            'padding: 6px 12px; border-radius: 999px;'
        )

    def set_tone(self, text: str, tone: str) -> None:
        self.setText(text)
        self.setStyleSheet(self._style(tone))


class WarningBanner(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setStyleSheet(
            'color: rgba(254,243,199,0.9); font-size: 11px; background: rgba(245,158,11,0.10); '
            'border: 1px solid rgba(245,158,11,0.25); border-radius: 10px; padding: 12px 14px;'
        )


class SettingRow(QWidget):
    """Label + optional hint on the left, control aligned right (legacy flex row)."""

    def __init__(
        self,
        title: str,
        *,
        subtitle: str = '',
        control: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(16)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f'color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent;'
        )
        text_col.addWidget(title_lbl)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(hint_style())
            text_col.addWidget(sub_lbl)
        layout.addLayout(text_col, 1)

        if control is not None:
            control.setMinimumWidth(148)
            control.setMaximumWidth(220)
            layout.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class PanelHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = '',
        *,
        badge_text: str = 'CS2',
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        badge = QLabel(badge_text)
        badge.setFixedSize(40, 40)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            'background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.10); '
            'border-radius: 10px; color: rgba(255,255,255,0.65); font-weight: 700; font-size: 11px;'
        )
        row.addWidget(badge)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(
            f'color: {TEXT}; font-size: 15px; font-weight: 700; background: transparent;'
        )
        col.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setWordWrap(True)
            s.setStyleSheet(hint_style())
            col.addWidget(s)
        row.addLayout(col, 1)


class StatCard(QFrame):
    """Legacy ai-engine-status tile."""

    def __init__(
        self,
        title: str,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty('frameRole', 'statCard')
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title = QLabel(title.upper())
        self._title.setStyleSheet(
            f'color: {TEXT_DIM}; font-size: 10px; font-weight: 600; '
            'letter-spacing: 0.12em; background: transparent;'
        )
        self._value = QLabel('—')
        self._value.setStyleSheet(
            f'color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent;'
        )
        self._sub = QLabel('')
        self._sub.setStyleSheet(
            'color: rgba(255,255,255,0.42); font-size: 10px; background: transparent;'
        )
        self._sub.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._sub)

    def set_values(self, value: str, sub: str = '') -> None:
        self._value.setText(value)
        self._sub.setText(sub)
        self._sub.setVisible(bool(sub))


def settings_card(title: str, subtitle: str = '', *, badge: str = 'CS2') -> tuple[QFrame, QVBoxLayout]:
    """Single legacy-style panel card + inner body layout."""
    card = make_card()
    outer = card_layout(card, margins=(22, 20, 22, 20))
    outer.setSpacing(0)
    outer.addWidget(PanelHeader(title, subtitle, badge_text=badge))
    outer.addSpacing(16)
    outer.addWidget(Divider())
    outer.addSpacing(12)
    body = QVBoxLayout()
    body.setSpacing(4)
    outer.addLayout(body)
    return card, body
