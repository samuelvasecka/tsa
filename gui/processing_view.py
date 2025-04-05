import importlib.util
import os
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QProgressBar, QVBoxLayout, QLabel
from data.data import get_indicators, get_data, set_results
from gui.state import State

# Trieda na asynchrónne detekovanie technických ukazovateľov
class WorkerThread(QThread):
    done: pyqtSignal = pyqtSignal()

    def run(self):
        initialize_indicators()
        self.done.emit()

# Trieda na analýzu časového radu a zobrazenia progress baru počas priebehu analýzy
class ProcessingView:
    def __init__(self, main_window):
        self.main_window = main_window

        self.main_window.progress_label = QLabel("Time series analysis in progress...")
        self.main_window.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.progress = QProgressBar()
        self.main_window.progress.setRange(0, 0)
        self.main_window.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_window.layout.addWidget(self.main_window.progress_label)
        self.main_window.layout.addWidget(self.main_window.progress)

        self.worker = WorkerThread()
        self.worker.finished.connect(self.on_processing_done)

    # Spustenie workeru, ktorý spustí detekciu jednotlivých technických ukazovateľov
    def start_processing(self):
        self.worker.start()

    # Metoda na presunutie na obrazovku s výsledkami po skončení analýzy
    def on_processing_done(self):
        self.main_window.set_state(State.RESULTS)
        self.main_window.results_plot_view.show_results()

# Metóda na inicializovanie všetkých ukazovateľov z priečinku /indicators
def initialize_indicators():
    files = get_indicators()
    indicator_classes = {}

    for file in files:
        file_path = os.path.join("./indicators", file + ".py")

        spec = importlib.util.spec_from_file_location(file, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            class_name = "".join(word.capitalize() for word in file.split("_"))
            if attr_name == class_name:
                attr = getattr(module, class_name)
                if isinstance(attr, type):
                    indicator_classes[file] = attr

    # Spustíme detekciu veštkých nájdených ukazovateľov
    start_indicators_detection(indicator_classes)

# Metóda na postupné spustenie detekcie nájdených ukazovateľov
def start_indicators_detection(indicator_classes):
    df = get_data()["data"]
    value_column = get_data()["value_column"]
    time_column = get_data()["time_column"]

    results = {}

    for file, indicator in indicator_classes.items():
        # Metódu detect obsahuje každý technický ukazovateľ
        results[file] = indicator.detect(indicator, df, value_column, time_column)

    time.sleep(1)
    set_results(results)