import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QCheckBox, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.dates import DateFormatter
from matplotlib.ticker import ScalarFormatter
from data.data import get_data, set_max_item
from gui.state import State

# Trieda na vlastnú navigačnú lišťu zobrazenú nad grafmi
class CustomNavigationToolbar(NavigationToolbar):

    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

        # Typy funkcií, ktoré chceme mať v navigačnej lište zobrazené
        # Home - resetovanie náhľadu
        # Pan - posúvanie sa v grafe
        # Zoom - približovanie v grafe
        # Save - export grafu v podobe obrázku
        allowed_tools = {"Home", "Pan", "Zoom", "Save"}

        for action in self.actions():
            if action.text() not in allowed_tools:
                self.removeAction(action)

# Trieda na zobrazovanie grafu
class PlotView:
    def __init__(self, main_window):
        self.main_window = main_window

        # Plátno na zobrazovanie grafu a ďalšie potrebné komponenty
        self.main_window.figure, self.main_window.ax = plt.subplots()
        self.main_window.canvas = FigureCanvas(self.main_window.figure)

        self.main_window.toolbar = CustomNavigationToolbar(self.main_window.canvas, self.main_window)

        self.main_window.layout.addWidget(self.main_window.toolbar)
        self.main_window.layout.addWidget(self.main_window.canvas)

        # Komponenty na používanie testového módu
        self.main_window.test_mode_checkbox = QCheckBox("Use test mode")
        self.main_window.layout.addWidget(self.main_window.test_mode_checkbox)
        self.main_window.test_mode_checkbox.stateChanged.connect(self.toggle_test_mode)

        self.main_window.row_count_label = QLabel("Number of rows:")
        self.main_window.row_count_input = QLineEdit()
        self.main_window.percent_label = QLabel("% of rows:")
        self.main_window.percent_input = QLineEdit()

        self.main_window.layout.addWidget(self.main_window.row_count_label)
        self.main_window.layout.addWidget(self.main_window.row_count_input)
        self.main_window.layout.addWidget(self.main_window.percent_label)
        self.main_window.layout.addWidget(self.main_window.percent_input)

        self.main_window.row_count_label.hide()
        self.main_window.row_count_input.hide()
        self.main_window.percent_label.hide()
        self.main_window.percent_input.hide()

        self.main_window.row_count_input.textChanged.connect(self.update_row_count)
        self.main_window.percent_input.textChanged.connect(self.update_percentage)

        self.main_window.go_to_select_indicators_button = QPushButton("Next")
        self.main_window.go_to_select_indicators_button.clicked.connect(lambda: self.main_window.set_state(State.SELECT_INDICATORS))
        self.main_window.layout.addWidget(self.main_window.go_to_select_indicators_button)

    # Metóda na vypnutie a zapnutie testového módu
    def toggle_test_mode(self, state):
        if state == 2:
            self.main_window.row_count_label.show()
            self.main_window.row_count_input.show()
            self.main_window.percent_label.show()
            self.main_window.percent_input.show()
        else:
            self.main_window.row_count_label.hide()
            self.main_window.row_count_input.hide()
            self.main_window.percent_label.hide()
            self.main_window.percent_input.hide()
            set_max_item(None)
        self.plot_data()

    # Metóda, ktorá upraví percentuálnú hodnotu, keď používateľ nastaví maximálny bod spracovania v grafe
    def update_percentage(self):
        try:
            df = get_data()["data"]
            total = len(df)
            percent = float(self.main_window.percent_input.text())

            if percent > 100:
                percent = 100
                self.main_window.percent_input.setText(str(percent))

            rows = total * (percent / 100)
            set_max_item(rows)
            self.main_window.row_count_input.textChanged.disconnect(self.update_row_count)
            self.main_window.row_count_input.setText(str(int(rows)))
            self.main_window.row_count_input.textChanged.connect(self.update_row_count)

            self.plot_data()
        except ValueError:
            pass

    # Metóda, ktorá upraví maximálny bod v grafe, keď používateľ nastaví percentuálnú hodnotu dát na spracovania
    def update_row_count(self):
        try:
            df = get_data()["data"]
            total = len(df)
            rows = float(self.main_window.row_count_input.text())

            if rows > total:
                rows = total
                self.main_window.row_count_input.setText(str(rows))

            percent = float((rows / total) * 100)
            set_max_item(rows)
            self.main_window.percent_input.textChanged.disconnect(self.update_percentage)
            self.main_window.percent_input.setText(f"{percent:.4f}")
            self.main_window.percent_input.textChanged.connect(self.update_percentage)

            self.plot_data()
        except ValueError:
            pass

    # Metóda na vykreslenie dát do grafu
    def plot_data(self):
        self.main_window.ax.clear()
        df = get_data()["data"]
        time_column, value_column = get_data()["time_column"], get_data()["value_column"]

        # Ak je časový stĺpec v nejakom stringovom dátumovom formáte, vytvoríme z neho vhodný typ
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            if not pd.to_numeric(df[time_column], errors='coerce').notna().all():
                df.loc[:, time_column] = pd.to_datetime(df[time_column], errors='coerce')

        # Testový mód je zapnutý
        if self.main_window.test_mode_checkbox.isChecked():
            try:
                count = int(self.main_window.row_count_input.text())
            except ValueError:
                count = 0

            if count + 1 <= len(df):
                df_filtered = df.iloc[:count]

                # Vykreslíme celé dáta sivou farbou
                self.main_window.ax.plot(df[time_column], df[value_column], linestyle='-', color='gray')

                # Nad to vykreslíme dáta ktoré ideme analyzovať čiernou farbou
                self.main_window.ax.plot(df_filtered[time_column], df_filtered[value_column], linestyle='-',
                             color='black')
                if count > 0:
                    x_value = df[time_column].iloc[count - 1]
                    y_min = df[value_column].min()
                    y_max = df[value_column].max()

                    # V mieste kde sa končí časť určená na analýzu vykreslíme zvyslú červenú čiaru
                    self.main_window.ax.vlines(x=x_value, ymin=y_min, ymax=y_max, colors='red', linestyles='dashed', label="End of data")
            else:
                self.main_window.ax.plot(df[time_column], df[value_column], linestyle='-', color='black')
        # Testový mód je vypnutý - vykreslíme data normálne čiernou farbou
        else:
            self.main_window.ax.plot(df[time_column], df[value_column], linestyle='-', color='black')

        self.main_window.ax.yaxis.set_major_formatter(ScalarFormatter())
        self.main_window.ax.yaxis.get_major_formatter().set_scientific(False)
        self.main_window.ax.set_xlabel("Time")
        self.main_window.ax.set_ylabel("Values")

        if pd.api.types.is_datetime64_any_dtype(df[time_column]):
            self.main_window.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))

        self.main_window.ax.figure.autofmt_xdate()
        self.main_window.canvas.draw()
