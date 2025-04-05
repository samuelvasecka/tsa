from enum import Enum
from PyQt6.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Enum trieda na navigovanie medzi obrazovkami
class State(Enum):
    IMPORT = 1
    FILE_CONFIRM = 2
    FILE_PREVIEW = 3
    SELECT_INDICATORS = 4
    PROCESSING = 5
    RESULTS = 6

# Trieda na zobrazovanie komponentov pre danú obrazovku
class StateManager:
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    # Metóda, ktorá pre vybranú obrazovku zobrazí potrebné komponenty
    def set_state(self, state):
        self.hide()
        if state is State.IMPORT:
            self.main_window.info_label.show()
            self.main_window.drag_drop_label.show()
            self.main_window.upload_button.show()
            self.main_window.example_button.show()
        elif state is State.FILE_CONFIRM:
            self.main_window.warning_label.show()
            self.main_window.table.show()
            self.main_window.has_header_checkbox.show()
            self.main_window.has_header_checkbox.setChecked(True)
            self.main_window.use_file_button.show()
            self.main_window.use_another_file_button.show()
        elif state is State.FILE_PREVIEW:
            self.main_window.canvas.show()
            self.main_window.toolbar.show()
            self.main_window.test_mode_checkbox.show()
            if self.main_window.test_mode_checkbox.isChecked():
                self.main_window.row_count_label.show()
                self.main_window.row_count_input.show()
                self.main_window.percent_label.show()
                self.main_window.percent_input.show()
            self.main_window.use_another_file_button.show()
            self.main_window.go_to_select_indicators_button.show()
        elif state is State.SELECT_INDICATORS:
            self.main_window.select_indicators_label.show()
            self.main_window.go_to_loading_button.show()
            for i in range(len(self.main_window.indicator_checkboxes)):
                self.main_window.indicator_checkboxes[i].show()
        elif state is State.PROCESSING:
            self.main_window.progress_label.show()
            self.main_window.progress.show()
        elif state is State.RESULTS:
            self.main_window.canvas.show()
            self.main_window.toolbar.show()
            for i in range(len(self.main_window.results_indicator_checkboxes)):
                self.main_window.results_indicator_checkboxes[i].show()
            self.main_window.use_another_file_button.show()

    # Metóda, ktorá schová všetky komponenty
    def hide(self):
        for child in self.main_window.findChildren(QWidget):
            if type(child) is not QWidget:
                if isinstance(child, QWidget):
                    child.hide()
                elif isinstance(child, FigureCanvas):
                    child.hide()