from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QFileDialog, QLabel
from utils.data_preproccesor import process_data
from gui.state import State

# Trieda na prechádzanie a nahranie lokálnych súborov, resp. výber ukážkového súboru
class FileLoader:
    def __init__(self, main_window):
        self.main_window = main_window

        # Jednotlivé komponenty ako tlačidlá a chybové hlášky a hlášky s upozorneniami
        self.main_window.upload_button = QPushButton("Upload File")
        self.main_window.upload_button.clicked.connect(self.open_file_dialog)

        self.main_window.example_button = QPushButton("Use Example Data")
        self.main_window.example_button.clicked.connect(lambda: self.load_file('data/example.csv'))

        self.main_window.layout.addWidget(self.main_window.upload_button)
        self.main_window.layout.addWidget(self.main_window.example_button)

        self.main_window.error_file_label = QLabel("Invalid file! Values column is missing, please provide correct file")
        self.main_window.error_file_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_window.error_file_label.setStyleSheet(
            "font-size: 14px; padding: 10px; color: white; background-color: red; border-radius: 5px;")
        self.main_window.error_file_label.hide()
        self.main_window.layout.insertWidget(0, self.main_window.error_file_label)

    # Metóda na otvorenie okna na prehľadávanie lokálnych súborov, akceptujeme iba CSV súbory
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, "Open File", "", "CSV Files (*.csv)")
        if file_path:
            self.load_file(file_path)

    # Metóda na potvrdenie vybraného súboru a presunutie na ďalšiu obrazovku
    def confirm_file(self):
        self.main_window.set_state(State.FILE_PREVIEW)
        self.main_window.plot_view.plot_data()

    # Metóda ktorá vypíše názov vybraného súboru a presunie používateľa na nasledujúcu obrazovku
    def load_file(self, file_path):
        self.main_window.file_path = file_path
        self.main_window.use_file_button.setText(f"Use the {file_path.split('/')[-1]} file")
        self.main_window.drag_drop_label.setText(f"Loaded: {file_path.split('/')[-1]}")
        self.main_window.use_file_button.clicked.connect(self.confirm_file)
        self.main_window.set_state(State.FILE_CONFIRM)
        self.initial_data_load(0)

    # Metóda na pred spracovanie dát zo súboru a ich validáciu pomocou metódy process_data z utils
    def initial_data_load(self, header):
        self.main_window.error_file_label.hide()
        self.main_window.table.show()
        self.main_window.use_file_button.setEnabled(True)

        is_correct_file, df, time_col, value_col, virtual_time_added, numeric_columns = process_data(self.main_window.file_path, header)

        # súbor je validný
        if is_correct_file:
            self.main_window.table_view.display_csv(df, time_col, value_col, virtual_time_added, numeric_columns)

        # súbor je nevalidný, zobrazíme chybovú hlášku
        else:
            self.main_window.error_file_label.show()
            self.main_window.table.hide()
            self.main_window.use_file_button.setEnabled(False)
