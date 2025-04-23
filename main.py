import sys
from PyQt6.QtWidgets import QApplication
from views.main_view_gui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())