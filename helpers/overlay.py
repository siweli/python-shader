import ctypes
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication
from helpers.shaders import OverlayGLWidget

def make_window_noninteractive(window):
    """
    Use Windows API (via ctypes) to modify the window's extended style so that:
        - It is layered.
        - It is transparent (click-through).
        - It does not activate (so it won't steal focus).
        - It is excluded from screen capture.
        - It remains topmost.
    """
    hwnd = int(window.winId())
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_NOACTIVATE = 0x08000000
    user32 = ctypes.windll.user32
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    new_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

    # Set layered window attributes (fully opaque).
    user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)

    # Exclude this window from screen capture.
    WDA_EXCLUDEFROMCAPTURE = 0x11
    user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

    # Ensure window is topmost without activation.
    HWND_TOPMOST = -1
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        0, 0, 0, 0,
        SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    )



class OverlayWindow(QMainWindow):
    def __init__(self, fps=30):
        super().__init__()
        self.setWindowTitle("Overlay")
        # Set window flags: frameless, always on top, tool window.
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        # Make the window background transparent.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Do not allow the window to accept focus.
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        # Force the window to appear only on the primary monitor.
        primary_screen = QGuiApplication.primaryScreen()
        self.setGeometry(primary_screen.geometry())
        self.showFullScreen()

        # After a short delay, apply Windows API modifications.
        QTimer.singleShot(100, lambda: make_window_noninteractive(self))

        # Create the OpenGL widget and set it as the central widget.
        self.gl_widget = OverlayGLWidget(self, fps=fps)
        self.setCentralWidget(self.gl_widget)

    def keyPressEvent(self, event):
        # Close the overlay when the NumLock key is pressed.
        if event.key() == Qt.Key_NumLock:
            self.close()