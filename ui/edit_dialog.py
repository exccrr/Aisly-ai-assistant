from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

class EditDialog(QDialog):
    def __init__(self, original_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать запрос")
        self.setMinimumWidth(500)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(original_text)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()
