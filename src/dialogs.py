from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)

class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Project name input
        layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
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