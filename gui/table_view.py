from PyQt6.QtWidgets import QTableWidget, QPushButton, QTableWidgetItem, QHeaderView, QCheckBox
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from data.data import set_data

MAX_ROWS = 5

# Trieda na zobrazenie náhľadu dát v tabuľkovom formáte
class TableView:
    def __init__(self, main_window):
        self.virtual_time_added = None
        self.time_col = None
        self.value_col = None
        self.df = None
        self.numeric_columns = None

        # Potrebné komponenty na vykreslenie tabuľky
        self.main_window = main_window
        self.main_window.table = QTableWidget()
        self.main_window.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.main_window.layout.addWidget(self.main_window.table)

        self.main_window.has_header_checkbox = QCheckBox("Has header (Please checked if provided file have header)")
        self.main_window.has_header_checkbox.setChecked(True)
        self.main_window.layout.addWidget(self.main_window.has_header_checkbox)
        self.main_window.has_header_checkbox.stateChanged.connect(self.toggle_has_header)

    # Vykreslenie tabuľky s dátami
    def display_csv(self, df, time_col, value_col, virtual_time_added, numeric_columns):
        self.df = df
        self.value_col = value_col
        self.time_col = time_col
        self.virtual_time_added = virtual_time_added
        self.numeric_columns = numeric_columns

        if virtual_time_added:
            self.main_window.warning_label.setVisible(True)
        else:
            self.main_window.warning_label.setVisible(False)

        if not value_col:
            self.main_window.use_file_button.setEnabled(False)
        else:
            self.main_window.use_file_button.setEnabled(True)

        if df is not None:
            rows = min(len(df), MAX_ROWS)
            self.main_window.table.setRowCount(rows + 3)
            self.main_window.table.setColumnCount(len(df.columns))

            # Nastavíme hlavičky - tlačidlá na výber daného stĺpcu a názvy stĺpcov
            for col, column_name in enumerate(df.columns):
                if time_col == df.columns[col]:
                    item = QTableWidgetItem("Time")
                    item.setBackground(QBrush(QColor("green")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.main_window.table.setItem(0, col, item)
                elif value_col is not None and value_col == column_name:
                    header_button = QPushButton("Values")
                    header_button.setStyleSheet("background-color: green; color: white;")
                    header_button.clicked.connect(lambda checked, c=column_name: self.select_value_column(df, c, time_col, virtual_time_added, numeric_columns))
                    self.main_window.table.setCellWidget(0, col, header_button)
                elif column_name not in numeric_columns:
                    item = QTableWidgetItem("Invalid column")
                    item.setBackground(QBrush(QColor("Red")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.main_window.table.setItem(0, col, item)
                else:
                    header_button = QPushButton("Use this column")
                    header_button.clicked.connect(lambda checked, c=column_name: self.select_value_column(df, c, time_col, virtual_time_added, numeric_columns))
                    self.main_window.table.setCellWidget(0, col, header_button)

                header = QTableWidgetItem(column_name)
                font = QFont()
                font.setBold(True)
                header.setFont(font)
                header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_window.table.setItem(1, col, header)

                # Ukážka prvých 5 riadkov z datasetu
                for row in range(0, rows):
                    item = QTableWidgetItem(str(df.iat[row, col]))
                    if virtual_time_added and col == 0:
                        item.setBackground(QBrush(QColor("orange")))
                        item.setForeground(QBrush(QColor("black")))
                    elif time_col == column_name:
                        item.setBackground(QBrush(QColor("green")))
                    elif column_name not in numeric_columns:
                        item.setBackground(QBrush(QColor("red")))
                    if value_col == column_name:
                        item.setBackground(QBrush(QColor("green")))
                    self.main_window.table.setItem(row + 2, col, item)

                item = QTableWidgetItem("...")
                self.main_window.table.setItem(rows + 2, col, item)

    # Metóda na vybratie konkrétneho stĺpca s hodnotami
    def select_value_column(self, df, value_col, time_col, virtual_time_added, numeric_columns):
        set_data(time_col, value_col, df[[time_col, value_col]])
        self.display_csv(df, time_col, value_col, virtual_time_added, numeric_columns)

    # Metóda na určenie, či dataset obsahuje hlavičku alebo nie
    def toggle_has_header(self, state):
        if state == 2:
            self.main_window.file_loader.initial_data_load(0)
        else:
            self.main_window.file_loader.initial_data_load(None)
