import os
from PyQt6.QtWidgets import QCheckBox, QLabel, QPushButton
from data.data import set_indicators
from gui.state import State
from indicators.technical_indicator import IndicatorEnums

# Meóda na načítanie všetkých dostupných ukazovateľov z priečinku /indicators
def load_classes_from_directory(directory):
    classes = []
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py" and filename != IndicatorEnums.ABSTRACT_INDICATOR.value:
            module_name = filename[:-3]
            classes.append(module_name)

    return classes

# Trieda na zobrazenie check boxov na výber ukazovateľov, ktoré chceme v dátach detekovať
class SelectIndicatorsView:
    def __init__(self, main_window):
        self.main_window = main_window
        indicators_dir = "./indicators"

        self.class_names = load_classes_from_directory(indicators_dir)
        self.main_window.select_indicators_label = QLabel("Please select all indicators which should be used for analysis")
        self.main_window.layout.addWidget(self.main_window.select_indicators_label)

        # Vytvorenie jednotlivých check boxov pre každý nájdený ukazovateľ
        self.main_window.indicator_checkboxes = []
        self.indicators = self.class_names
        set_indicators(self.indicators)
        for class_name in self.class_names:
            self.main_window.indicator_checkboxes.append(QCheckBox(class_name.replace("_", " ").capitalize()))
            self.main_window.indicator_checkboxes[-1].setChecked(True)
            self.main_window.indicator_checkboxes[-1].stateChanged.connect(lambda state, name = class_name: self.toggle_indicator(state, name))
            self.main_window.layout.addWidget(self.main_window.indicator_checkboxes[-1])

        self.main_window.go_to_loading_button = QPushButton("Confirm")
        self.main_window.go_to_loading_button.clicked.connect(
            lambda: self.go_to_processing())
        self.main_window.layout.addWidget(self.main_window.go_to_loading_button)

    # Metóda na potvrdenie vybratých ukazovateľov a presmerovanie na ďalšiu obrazovku
    def go_to_processing(self):
        self.main_window.set_state(State.PROCESSING)
        self.main_window.processing_view.start_processing()

    # Metóda na vybratie/zrušenie použitia daného ukazovateľa
    def toggle_indicator(self, state, name):
        if state == 2:
            self.indicators.append(name)
        else:
            self.indicators.remove(name)

        if len(self.indicators) <= 0:
            self.main_window.go_to_loading_button.setEnabled(False)
        else:
            self.main_window.go_to_loading_button.setEnabled(True)

        set_indicators(self.indicators)
