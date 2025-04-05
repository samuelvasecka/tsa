import importlib.util
import os
import pandas as pd
from PyQt6.QtWidgets import QCheckBox
from matplotlib.dates import DateFormatter
from matplotlib.ticker import ScalarFormatter
from data.data import get_results, get_data, get_max_item

# Trieda na vykreslenie grafu s výsledkami
class ResultsPlotView:
    def __init__(self, main_window):
        self.main_window = main_window

        self.main_window.results_indicator_checkboxes = []
        self.are_results_shown = {}
        self.results = {}

    # Metóda na vytvorneie check boxov, ktoré určujú, ktoré výsledky, ktorých technických ukazovateľov budú zobrazené v grafe
    def show_results(self):
        for widget in self.main_window.results_indicator_checkboxes:
            self.main_window.layout.removeWidget(widget)
            widget.deleteLater()

        self.main_window.results_indicator_checkboxes = []

        self.are_results_shown = {}
        self.plot_results()

        self.results = get_results()

        for file, result in self.results.items():
            self.main_window.results_indicator_checkboxes.append(
                QCheckBox("Show results for: " + (file.replace("_", " ").capitalize()) + (
                    " (Pattern detected)" if result["detected"] else " (Patter not detected)")))
            self.main_window.results_indicator_checkboxes[-1].setChecked(False)
            self.main_window.results_indicator_checkboxes[-1].stateChanged.connect(
                lambda state, name=file: self.toggle_indicator(state, name))
            self.main_window.layout.addWidget(self.main_window.results_indicator_checkboxes[-1])
            self.are_results_shown[file] = False

        self.main_window.layout.removeWidget(self.main_window.use_another_file_button)
        self.main_window.layout.addWidget(self.main_window.use_another_file_button)

    # Metóda na vypnutie/zapnutie zobrazenia výsledkov daného indikátoru
    def toggle_indicator(self, state, name):
        if state == 2:
            self.are_results_shown[name] = True
        else:
            self.are_results_shown[name] = False

        self.plot_results()

    # Metóda na vykreslenie dát a vybraných výsledkov
    def plot_results(self):
        self.main_window.ax.clear()
        df = get_data()["data"]
        max_item = get_max_item()
        time_column, value_column = get_data()["time_column"], get_data()["value_column"]

        # Ak je časový stĺpec v nejakom stringovom dátumovom formáte, vytvoríme z neho vhodný typ
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            if not pd.to_numeric(df[time_column], errors='coerce').notna().all():
                df.loc[:, time_column] = pd.to_datetime(df[time_column], errors='coerce')

        if max_item is not None:
            df_filtered = df.iloc[:max_item]

            # Vykreslíme celé dáta sivou farbou
            self.main_window.ax.plot(df[time_column], df[value_column], linestyle='-', color='gray')

            # Nad to vykreslíme dáta ktoré ideme analyzovať čiernou farbou
            self.main_window.ax.plot(df_filtered[time_column], df_filtered[value_column], linestyle='-',
                                     color='black')
            if max_item > 0:
                x_value = df[time_column].iloc[max_item - 1]
                y_min = df[value_column].min()
                y_max = df[value_column].max()

                # V mieste kde sa končí časť určená na analýzu vykreslíme zvyslú červenú čiaru
                self.main_window.ax.vlines(x=x_value, ymin=y_min, ymax=y_max, colors='red', linestyles='dashed', label="End of data")

        # Testový mód je vypnutý - vykreslíme data normálne čiernou farbou
        else:
            self.main_window.ax.plot(df[time_column], df[value_column], linestyle='-', color='black')

        # Cyklus prejde cez výsledky jednotlivých ukazovateľov a vykreslí vybrané z nich
        for file, result in self.results.items():
            if self.are_results_shown.get(file):
                file_path = os.path.join("./indicators", file + ".py")

                spec = importlib.util.spec_from_file_location(file, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    class_name = "".join(word.capitalize() for word in file.split("_"))
                    if attr_name == class_name:
                        attr = getattr(module, class_name)
                        if isinstance(attr, type):

                            # Vykreslíme nájdené výsledky - metódu show,obsahuje každý indikátor
                            attr.show(attr, result, self.main_window, df)

        self.main_window.ax.yaxis.set_major_formatter(ScalarFormatter())
        self.main_window.ax.yaxis.get_major_formatter().set_scientific(False)
        self.main_window.ax.set_xlabel("Time")
        self.main_window.ax.set_ylabel("Values")

        if pd.api.types.is_datetime64_any_dtype(df[time_column]):
            self.main_window.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))

        self.main_window.ax.figure.autofmt_xdate()
        self.main_window.ax.legend()
        self.main_window.canvas.draw()
