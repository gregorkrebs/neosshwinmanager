"""
window_resizer.py – WM_NCHITTEST / WM_NCCALCSIZE handler for frameless windows.

WindowResizer is a pure-logic helper (no Qt widget) that processes Windows
native messages for a QMainWindow that uses FramelessWindowHint.

Usage
-----
    resizer = WindowResizer()
    resizer.set_titlebar_height(CustomTitleBar.HEIGHT)

    # In host window:
    def nativeEvent(self, event_type, message):
        handled, result = self._resizer.handle_native_event(self, event_type, message)
        if handled:
            return True, result
        return super().nativeEvent(event_type, message)

    # After every resize:
    resizer.update_btn_rects(list_of_QRect_window_local)
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes

# ── Windows message / hit-test constants ─────────────────────────────────────

_WM_NCHITTEST  = 0x0084
_WM_NCCALCSIZE = 0x0083

_HTCLIENT      = 1
_HTCAPTION     = 2
_HTLEFT        = 10
_HTRIGHT       = 11
_HTTOP         = 12
_HTTOPLEFT     = 13
_HTTOPRIGHT    = 14
_HTBOTTOM      = 15
_HTBOTTOMLEFT  = 16
_HTBOTTOMRIGHT = 17


class _MSG(ctypes.Structure):
    """Mirrors the Windows MSG struct for 64-bit processes."""
    _fields_ = [
        ("hWnd",    ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam",  ctypes.c_size_t),
        ("lParam",  ctypes.c_size_t),   # treated as unsigned; sign handled below
        ("time",    ctypes.c_ulong),
        ("pt",      ctypes.wintypes.POINT),
    ]


def _loword(val: int) -> int:
    """Extract signed low 16-bit value from a packed Windows LPARAM."""
    v = val & 0xFFFF
    return v - 0x10000 if v >= 0x8000 else v


def _hiword(val: int) -> int:
    """Extract signed high 16-bit value from a packed Windows LPARAM."""
    v = (val >> 16) & 0xFFFF
    return v - 0x10000 if v >= 0x8000 else v


# ── main class ───────────────────────────────────────────────────────────────

class WindowResizer:
    """
    Processes WM_NCHITTEST and WM_NCCALCSIZE for a frameless QMainWindow.

    The host window must:
    1. Call handle_native_event() from nativeEvent().
    2. Call update_btn_rects() after every layout / resize so button
       hit areas stay current.
    3. Call set_titlebar_height() once during setup.

    Hit-test logic:
    - Near any window edge → appropriate HT resize code (native resize).
    - Over a titlebar button → HTCLIENT (Qt handles clicks).
    - Titlebar caption area → HTCAPTION (Windows drag + Snap).
    - Everywhere else → HTCLIENT.

    WM_NCCALCSIZE (wParam=1) returns 0 to extend the client area to the
    full window rect while keeping WS_THICKFRAME (shadow-only).
    """

    # Grab-band width in pixels.  8 px works well across 100–200 % DPI.
    RESIZE_BORDER: int = 8

    def __init__(self) -> None:
        self._btn_rects: list[tuple[int, int, int, int]] = []
        self._titlebar_height: int = 36

    # ── configuration ────────────────────────────────────────────────────────

    def set_titlebar_height(self, h: int) -> None:
        self._titlebar_height = h

    def update_btn_rects(self, rects: list) -> None:
        """
        Store button hit areas as window-local (x, y, w, h) tuples.
        *rects* is a list of QRect objects in window-local coordinates.
        """
        self._btn_rects = [
            (r.x(), r.y(), r.width(), r.height()) for r in rects
        ]

    # ── entry point ──────────────────────────────────────────────────────────

    def handle_native_event(
        self,
        window,           # QMainWindow instance
        event_type: bytes,
        message: object,
    ) -> tuple[bool, int]:
        """
        Returns (handled, result).
        If handled is True the caller must return (True, result) from nativeEvent.

        PyQt6 passes *message* as a sip.voidptr.  We must cast it to a
        ctypes pointer rather than using from_address(), which causes an
        access violation on 64-bit builds.
        """
        if event_type != b"windows_generic_MSG":
            return False, 0

        try:
            # sip.voidptr exposes __int__() which is the raw C pointer value.
            # Cast to a ctypes pointer-to-MSG so we can read fields safely.
            ptr = ctypes.cast(int(message), ctypes.POINTER(_MSG))
            msg = ptr.contents
        except Exception:
            return False, 0

        if msg.message == _WM_NCCALCSIZE and msg.wParam:
            # Return 0: client area = entire window rect.
            # WS_THICKFRAME is kept only for the DWM drop shadow.
            return True, 0

        if msg.message == _WM_NCHITTEST:
            return self._hit_test(window, msg.lParam)

        return False, 0

    # ── hit-testing ──────────────────────────────────────────────────────────

    def _hit_test(self, window, lp: int) -> tuple[bool, int]:
        from PyQt6.QtCore import Qt

        cx = _loword(lp)
        cy = _hiword(lp)

        # Window top-left in screen coordinates
        pos = window.pos()
        wx  = cx - pos.x()
        wy  = cy - pos.y()
        ww  = window.width()
        wh  = window.height()

        maximized = bool(
            window.windowState() & Qt.WindowState.WindowMaximized
        )

        b = self.RESIZE_BORDER

        # ── resize borders (ignored when maximized) ──────────────────────
        if not maximized:
            in_top    = wy < b
            in_bottom = wy >= wh - b
            in_left   = wx < b
            in_right  = wx >= ww - b

            if in_top and in_left:
                return True, _HTTOPLEFT
            if in_top and in_right:
                return True, _HTTOPRIGHT
            if in_bottom and in_left:
                return True, _HTBOTTOMLEFT
            if in_bottom and in_right:
                return True, _HTBOTTOMRIGHT
            if in_left:
                return True, _HTLEFT
            if in_right:
                return True, _HTRIGHT
            if in_top:
                return True, _HTTOP
            if in_bottom:
                return True, _HTBOTTOM

        # ── titlebar control buttons → HTCLIENT so Qt handles clicks ─────
        for (bx, by, bw, bh) in self._btn_rects:
            if bx <= wx < bx + bw and by <= wy < by + bh:
                return True, _HTCLIENT

        # ── caption band → HTCLIENT so Qt handles mouse events ───────────
        # We use HTCLIENT (not HTCAPTION) to avoid Windows posting WM_SYSCOMMAND
        # SC_MOVE/SC_SIZE or showing the system menu on right-click, which causes
        # a C++ crash in Qt's frameless-window handling.  Native drag + Snap is
        # triggered from CustomTitleBar.mouseMoveEvent via QWindow.startSystemMove().
        if 0 <= wy < self._titlebar_height:
            return True, _HTCLIENT

        return True, _HTCLIENT
