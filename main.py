import os.path
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), "static", "icon.ico")
    app.setWindowIcon(QIcon(icon_path))
    widget = MainWindow(app=app)
    widget.show()
    sys.exit(app.exec())
