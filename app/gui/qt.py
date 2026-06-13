"""Qt6 bindings — prefer PySide6, fall back to PyQt6."""

from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QFont, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QStatusBar,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    QT_API = 'PySide6'
except ModuleNotFoundError:
    try:
        from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal
        from PyQt6.QtGui import QFont, QPixmap
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QFrame,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QPushButton,
            QScrollArea,
            QSlider,
            QSpinBox,
            QStatusBar,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )

        QT_API = 'PyQt6'
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            'GUI requires PySide6 (recommended) or PyQt6. '
            'Run: .venv\\Scripts\\pip install PySide6'
        ) from exc

__all__ = [
    'QApplication',
    'QCheckBox',
    'QComboBox',
    'QDoubleSpinBox',
    'QFileDialog',
    'QFont',
    'QFormLayout',
    'QFrame',
    'QGridLayout',
    'QGroupBox',
    'QHBoxLayout',
    'QLabel',
    'QLineEdit',
    'QMainWindow',
    'QPixmap',
    'QPushButton',
    'QScrollArea',
    'QSlider',
    'QSpinBox',
    'QStatusBar',
    'QTabWidget',
    'QTimer',
    'QT_API',
    'Qt',
    'QVBoxLayout',
    'QWidget',
    'Signal',
]
