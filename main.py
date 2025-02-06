import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QSurfaceFormat
from helpers.overlay import OverlayWindow

# set fps here
fps = 144

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set up the desired OpenGL format.
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = OverlayWindow(fps=fps)
    window.show()
    sys.exit(app.exec_())
