from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QComboBox, QScrollArea, QSpinBox


class NoWheelComboBox(QComboBox):
    """ComboBox that ignores wheel events unconditionally to prevent accidental changes."""

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class NoWheelSpinBox(QSpinBox):
    """SpinBox that ignores wheel events unconditionally to prevent accidental changes."""

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class NoWheelScrollArea(QScrollArea):
    """ScrollArea that handles wheel events normally."""
    pass


class NoWheelFilter:
    """
    Optional event filter that can be installed on widgets if needed.
    Currently unused, but kept as a simple alternative to subclassing.
    """

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() == QEvent.Type.Wheel:
            return True
        return False

