"""Native Qt main window — legacy AimSync shell."""

from __future__ import annotations

from app.core.config import config_path
from app.core.identity import APP_DISPLAY_NAME, APP_VERSION
from app.gui.ai_panel import AiPanel
from app.gui.global_panel import GlobalPanel
from app.gui.qt import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPixmap,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from app.gui.recoil_panel import RecoilPanel
from app.gui.theme import ACCENT_BLUE, BG_ELEVATED, logo_path, style_stop_button
from app.gui.widgets import StatusBadge
from app.makcu.manager import makcu_manager


class MainWindow(QMainWindow):
    def __init__(self, *, dev_mode: bool = False) -> None:
        super().__init__()
        self._dev_mode_allowed = dev_mode
        self.setWindowTitle(f'{APP_DISPLAY_NAME}  ·  v{APP_VERSION}')
        self.resize(960, 860)
        self.setMinimumSize(720, 680)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QWidget()
        nav.setStyleSheet(
            f'background: {BG_ELEVATED}; border-bottom: 1px solid rgba(255,255,255,0.08);'
        )
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(24, 14, 24, 14)
        nav_layout.setSpacing(14)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(48, 48)
        logo_lbl.setScaledContents(True)
        logo_file = logo_path()
        if logo_file is not None:
            pix = QPixmap(str(logo_file))
            if not pix.isNull():
                logo_lbl.setPixmap(pix)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(2)
        brand = QLabel(APP_DISPLAY_NAME)
        brand.setStyleSheet(
            'font-size: 17px; font-weight: 700; color: #fafafa; background: transparent;'
        )
        version = QLabel(f'{APP_VERSION} · Dual-PC CS2')
        version.setStyleSheet(
            f'color: {ACCENT_BLUE}; font-size: 10px; font-weight: 600; '
            'letter-spacing: 0.06em; text-transform: uppercase; background: transparent;'
        )
        brand_col.addWidget(brand)
        brand_col.addWidget(version)

        nav_layout.addWidget(logo_lbl)
        nav_layout.addLayout(brand_col)
        nav_layout.addStretch(1)

        self._stop_btn = QPushButton('Stop App')
        self._stop_btn.setFixedWidth(96)
        style_stop_button(self._stop_btn)
        self._stop_btn.clicked.connect(self.close)
        nav_layout.addWidget(self._stop_btn)
        layout.addWidget(nav)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 0)
        content_layout.setSpacing(0)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        self._global_panel = GlobalPanel()
        global_scroll = QScrollArea()
        global_scroll.setWidgetResizable(True)
        global_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        global_scroll.setWidget(self._global_panel)
        tabs.addTab(global_scroll, 'Global Settings')

        self._recoil_panel = RecoilPanel(compact=True)
        recoil_scroll = QScrollArea()
        recoil_scroll.setWidgetResizable(True)
        recoil_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        recoil_scroll.setWidget(self._recoil_panel)
        tabs.addTab(recoil_scroll, 'Game Engine')

        self._ai_panel = AiPanel()
        ai_scroll = QScrollArea()
        ai_scroll.setWidgetResizable(True)
        ai_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        ai_scroll.setWidget(self._ai_panel)
        tabs.addTab(ai_scroll, 'AimSync AI')
        content_layout.addWidget(tabs, 1)
        layout.addWidget(content, 1)

        footer = QWidget()
        footer.setStyleSheet(
            f'background: {BG_ELEVATED}; border-top: 1px solid rgba(255,255,255,0.08);'
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 10, 24, 10)
        self._badge_input = StatusBadge('MAKCU: —', tone='info')
        self._badge_mode = StatusBadge('DUAL-PC: —', tone='warn')
        footer_layout.addWidget(self._badge_input)
        footer_layout.addWidget(self._badge_mode)
        footer_layout.addStretch(1)
        copy_lbl = QLabel('© 2026 AimSync')
        copy_lbl.setStyleSheet('color: rgba(255,255,255,0.28); font-size: 10px;')
        footer_layout.addWidget(copy_lbl)
        layout.addWidget(footer)

        cfg_hint = QLabel(f'Config: {config_path()}')
        cfg_hint.setStyleSheet(
            'color: rgba(255,255,255,0.22); font-size: 10px; padding: 4px 24px 8px;'
        )
        cfg_hint.setWordWrap(True)
        layout.addWidget(cfg_hint)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._refresh_footer)
        self._timer.start()

        self.refresh_makcu_status()

    def refresh_makcu_status(self) -> None:
        dev = makcu_manager.dev_mode
        self._global_panel.set_dev_warning(dev or self._dev_mode_allowed)
        self._refresh_footer()

    def _refresh_footer(self) -> None:
        if makcu_manager.is_hardware():
            self._badge_input.set_tone('MAKCU: CONNECTED', 'ok')
            self._badge_mode.set_tone('DUAL-PC: READY', 'ok')
        elif makcu_manager.dev_mode:
            self._badge_input.set_tone('MAKCU: DEV MODE', 'warn')
            self._badge_mode.set_tone('DUAL-PC: LOCAL MOUSE', 'warn')
        else:
            err = (makcu_manager.last_error or 'NOT FOUND')[:24].upper()
            self._badge_input.set_tone(f'MAKCU: {err}', 'bad')
            self._badge_mode.set_tone('DUAL-PC: OFFLINE', 'bad')
