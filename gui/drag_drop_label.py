from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

# Trieda slúžiaca ako komponentpre funkciu drag and drop pri nahrávaní súborov
class DragDropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Drag & Drop CSV file here")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px dashed gray; padding: 20px; font-size: 14px;")
        self.setAcceptDrops(True)

    # Event na detekciu, že sa súbor presunul do drag and drop časti
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # Event na detekciu, že bol súbor nahraný promocou drag an drop funkcie
    # Uložíme si cestu k nahranému súboru
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.window().file_loader.load_file(file_path)
