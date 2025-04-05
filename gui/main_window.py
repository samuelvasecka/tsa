from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTableWidget

from gui.processing_view import ProcessingView
from gui.results_plot_view import ResultsPlotView
from gui.select_indicators_view import SelectIndicatorsView
from gui.state import StateManager, State
from gui.drag_drop_label import DragDropLabel
from gui.file_loader import FileLoader
from gui.table_view import TableView
from gui.plot_view import PlotView

# Hlavná trieda na zobrazovanie používateľského rozhrania
class MainWindow(QMainWindow):
    file_path = ""

    # V konštruktore načítame všetky potrebné komponenty, ktoré budeme zobrazovať hneď alebo aj neskôr
    def __init__(self):
        super().__init__()
        self.progress_label = None
        self.setWindowTitle("Time Series Analyzer")
        self.resize(700, 500)

        self.state_manager = StateManager(self)

        self.layout = QVBoxLayout()

        self.plot_view = PlotView(self)

        self.info_label = QLabel("Please upload a file with time series data or use example data")
        self.layout.addWidget(self.info_label)

        self.warning_label = QLabel("Virtual column for time was added!")
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.warning_label.setStyleSheet(
            "font-size: 14px; padding: 10px; color: black; background-color: orange; border-radius: 5px;")
        self.layout.addWidget(self.warning_label)

        self.drag_drop_label = DragDropLabel(self)
        self.layout.addWidget(self.drag_drop_label)

        self.file_loader = FileLoader(self)

        self.table_view = TableView(self)

        self.use_file_button = QPushButton()
        self.layout.addWidget(self.use_file_button)

        self.select_indicators_view = SelectIndicatorsView(self)

        self.processing_view = ProcessingView(self)

        self.use_another_file_button = QPushButton("Use another file")
        self.use_another_file_button.clicked.connect(lambda: self.set_state(State.IMPORT))
        self.layout.addWidget(self.use_another_file_button)

        self.results_plot_view = ResultsPlotView(self)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.set_state(State.IMPORT)

    # Metóda na zmenu obrazovky
    def set_state(self, state):
        self.state_manager.set_state(state)