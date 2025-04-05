import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

# Spustenie aplikácie
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())