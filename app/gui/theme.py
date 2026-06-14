"""Shared Qt styling — legacy KryptAim web UI palette."""

from __future__ import annotations

from pathlib import Path

from app.gui.qt import QApplication, QFont, QFormLayout, QFrame, QGroupBox, Qt, QVBoxLayout, QWidget

# Legacy Tailwind neutrals + accents
BG = '#0a0a0a'
BG_ELEVATED = '#171717'
BG_CARD = '#171717'
BG_INPUT = '#262626'
BG_MUTED = '#1f1f1f'
BORDER = 'rgba(255,255,255,0.10)'
BORDER_AMBER = 'rgba(251,191,36,0.25)'
TEXT = '#fafafa'
TEXT_MUTED = 'rgba(255,255,255,0.55)'
TEXT_DIM = 'rgba(255,255,255,0.40)'
ACCENT_BLUE = '#3b82f6'
ACCENT_AMBER = '#fbbf24'
ACCENT_AMBER_DARK = '#f59e0b'
ACCENT_EMERALD = '#34d399'
ACCENT_GREEN = '#4ade80'
ACCENT_RED = '#f87171'


def logo_path() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    for candidate in (
        root / 'assets' / 'KryptAim_logo.png',
        root.parent / 'Server' / 'logo' / 'KryptAim_logo.png',
    ):
        if candidate.is_file():
            return candidate
    return None


APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {BG_ELEVATED};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: #404040;
    min-height: 28px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QTabWidget::pane {{
    border: none;
    background: transparent;
    top: 0;
}}
QTabBar {{
    background: {BG_ELEVATED};
    border-bottom: 1px solid rgba(255,255,255,0.08);
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 12px 20px;
    margin: 0;
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 100px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT_BLUE};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
    border-bottom: 2px solid rgba(59,130,246,0.35);
}}
QTabBar::tab:last:selected {{
    color: {ACCENT_AMBER};
    border-bottom: 2px solid {ACCENT_AMBER};
}}
QCheckBox[switch="true"] {{
    spacing: 0;
}}
QCheckBox[switch="true"]::indicator {{
    width: 44px;
    height: 24px;
    border-radius: 12px;
    background: #3f3f46;
    border: 1px solid rgba(255,255,255,0.14);
}}
QCheckBox[switch="true"]::indicator:checked {{
    background: {ACCENT_AMBER_DARK};
    border-color: {ACCENT_AMBER};
}}
QCheckBox[switchAccent="blue"]::indicator:checked {{
    background: {ACCENT_BLUE};
    border-color: #60a5fa;
}}
QCheckBox[switch="true"]::indicator:unchecked:hover {{
    background: #52525b;
}}
QGroupBox {{
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    margin-top: 0;
    padding: 16px;
    background: {BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: {TEXT};
    background: {BG_CARD};
}}
QFormLayout QLabel {{
    color: {TEXT_DIM};
    font-size: 12px;
    font-weight: 500;
    background: transparent;
    min-width: 120px;
}}
QLineEdit {{
    background: {BG_INPUT};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 34px;
    color: {TEXT};
}}
QLineEdit:focus {{
    border-color: rgba(59,130,246,0.45);
}}
QComboBox, QDoubleSpinBox, QSpinBox {{
    background: {BG_INPUT};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 36px;
    color: {TEXT};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 18px;
    border: none;
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    margin: 2px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background: rgba(255,255,255,0.12);
}}
QLabel {{ color: #d4d4d4; background: transparent; }}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: rgba(59,130,246,0.45);
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {BG_INPUT};
    border: 1px solid rgba(255,255,255,0.12);
    selection-background-color: {ACCENT_AMBER_DARK};
    selection-color: #111;
    outline: none;
}}
QCheckBox {{ spacing: 10px; min-height: 28px; color: {TEXT_MUTED}; }}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.20);
    background: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_AMBER_DARK};
    border-color: {ACCENT_AMBER};
}}
QPushButton {{
    background: rgba(255,255,255,0.06);
    color: {TEXT};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 8px 16px;
    min-height: 34px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: rgba(255,255,255,0.10);
    border-color: rgba(255,255,255,0.18);
}}
QPushButton:pressed {{
    background: rgba(255,255,255,0.04);
}}
QPushButton:disabled {{
    color: rgba(255,255,255,0.35);
    background: rgba(255,255,255,0.03);
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: #333333;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 16px;
    margin: -5px 0;
    background: {ACCENT_AMBER_DARK};
    border-radius: 8px;
}}
QStatusBar {{
    background: {BG_ELEVATED};
    color: {TEXT_DIM};
    border-top: 1px solid rgba(255,255,255,0.06);
    padding: 4px 8px;
}}
QFrame[frameRole="card"] {{
    background: #141414;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
}}
QFrame[frameRole="cardAmber"] {{
    background: rgba(251,191,36,0.04);
    border: 1px solid {BORDER_AMBER};
    border-radius: 12px;
}}
QFrame[frameRole="statCard"] {{
    background: rgba(10,10,10,0.65);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
}}
"""


def make_group(title: str) -> QWidget:
    """Section card — QGroupBox when titled, plain card frame when not."""
    if title.strip():
        return QGroupBox(title.strip())
    frame = make_card()
    frame.setProperty('panelRole', 'untitled')
    return frame


def bootstrap_application(app: QApplication) -> None:
    """Fusion style + crisp fonts."""
    app.setStyle('Fusion')
    font = QFont('Segoe UI', 10)
    if hasattr(QFont, 'HintingPreference'):
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)
    app.setStyleSheet(APP_STYLESHEET)


def make_card(parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setProperty('frameRole', 'card')
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    return frame


def make_amber_card(parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setProperty('frameRole', 'cardAmber')
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    return frame


def card_layout(frame: QFrame, *, margins: tuple[int, int, int, int] = (20, 18, 20, 18)) -> QVBoxLayout:
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(*margins)
    layout.setSpacing(14)
    return layout


def setup_form(form: QFormLayout) -> None:
    form.setVerticalSpacing(14)
    form.setHorizontalSpacing(16)
    form.setContentsMargins(2, 4, 2, 2)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)


def style_primary_button(btn) -> None:
    btn.setStyleSheet(
        f'QPushButton {{ background: {ACCENT_AMBER}; color: #1c1917; border: 1px solid #fcd34d; '
        f'font-weight: 700; }} QPushButton:hover {{ background: #fcd34d; }}'
    )


def style_secondary_button(btn) -> None:
    btn.setStyleSheet(
        f'QPushButton {{ background: rgba(217,119,6,0.75); color: white; '
        f'border: 1px solid rgba(251,191,36,0.35); font-weight: 600; }} '
        f'QPushButton:hover {{ background: rgba(217,119,6,0.95); }}'
    )


def style_danger_button(btn) -> None:
    btn.setStyleSheet(
        'QPushButton { background: rgba(239,68,68,0.18); color: #fecaca; '
        'border: 1px solid rgba(248,113,113,0.35); font-weight: 600; } '
        'QPushButton:hover { background: rgba(239,68,68,0.28); }'
    )


def style_ghost_button(btn) -> None:
    btn.setStyleSheet(
        'QPushButton { background: rgba(59,130,246,0.10); color: #93c5fd; '
        'border: 1px solid rgba(59,130,246,0.25); font-weight: 600; } '
        'QPushButton:hover { background: rgba(59,130,246,0.18); }'
    )


def section_title(text: str, *, color: str = ACCENT_EMERALD) -> str:
    return (
        f'font-size: 12px; font-weight: 700; letter-spacing: 0.08em; '
        f'text-transform: uppercase; color: {color}; background: transparent;'
    )


def hint_style() -> str:
    return f'color: {TEXT_DIM}; font-size: 11px; background: transparent;'


def style_stop_button(btn) -> None:
    btn.setStyleSheet(
        'QPushButton { background: rgba(239,68,68,0.15); color: #fecaca; '
        'border: 1px solid rgba(248,113,113,0.35); font-weight: 700; font-size: 12px; } '
        'QPushButton:hover { background: rgba(239,68,68,0.28); }'
    )
