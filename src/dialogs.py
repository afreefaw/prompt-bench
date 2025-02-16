from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox
)
from parsers import discover_parsers

class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.parsers = discover_parsers()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Project name input
        layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        # Parser selection
        layout.addWidget(QLabel("Input Parser:"))
        self.parser_combo = QComboBox()
        if self.parsers:
            self.parser_combo.addItems(self.parsers.keys())
        else:
            self.parser_combo.addItem("No parsers available")
            self.parser_combo.setEnabled(False)
        layout.addWidget(self.parser_combo)
        
        # Buttons
        button_layout = QVBoxLayout()
        create_button = QPushButton("Create")
        create_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Set minimum size
        self.setMinimumWidth(300)
    
    def get_project_name(self) -> str:
        return self.name_input.text().strip()
    
    def get_selected_parser(self) -> str:
        """Get the selected parser type"""
        if not self.parsers:
            return None
        return self.parser_combo.currentText()