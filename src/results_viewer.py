from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QTextEdit, QLabel, QComboBox,
    QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
from typing import Dict, Optional

class ResultsViewer(QWidget):
    def __init__(self, test_run: Dict, parent=None):
        super().__init__(parent)
        self.test_run = test_run
        self.current_result = None
        self.setup_ui()
        self.load_results()
    
    def setup_ui(self):
        """Setup the results viewer UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"Test Results - Run ID: {self.test_run['runId']}")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Main content
        content = QHBoxLayout()
        
        # Left side - Results list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self.on_result_selected)
        
        left_layout.addWidget(QLabel("Results:"))
        left_layout.addWidget(self.results_list)
        
        # Right side - Result details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Context
        right_layout.addWidget(QLabel("Context:"))
        self.context_view = QTextEdit()
        self.context_view.setReadOnly(True)
        right_layout.addWidget(self.context_view)
        
        # Model response
        right_layout.addWidget(QLabel("Model Response:"))
        self.response_view = QTextEdit()
        self.response_view.setReadOnly(True)
        right_layout.addWidget(self.response_view)
        
        # Validation controls
        validation_layout = QHBoxLayout()
        
        self.success_btn = QPushButton("✓ Success")
        self.success_btn.clicked.connect(lambda: self.validate_result(True))
        self.fail_btn = QPushButton("✗ Fail")
        self.fail_btn.clicked.connect(lambda: self.validate_result(False))
        
        validation_layout.addWidget(self.success_btn)
        validation_layout.addWidget(self.fail_btn)
        right_layout.addLayout(validation_layout)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.show_previous)
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.show_next)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        right_layout.addLayout(nav_layout)
        
        # Add panels to content layout
        content.addWidget(left_panel, 1)
        content.addWidget(right_panel, 2)
        layout.addLayout(content)
    
    def load_results(self):
        """Load results into the list widget"""
        self.results_list.clear()
        for i, result in enumerate(self.test_run["results"], 1):
            status = ""
            if "validation" in result:
                status = " ✓" if result["validation"]["status"] else " ✗"
            self.results_list.addItem(f"Result {i}{status}")
        
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def on_result_selected(self, current, previous):
        """Handle result selection"""
        if current is None:
            return
        
        row = self.results_list.row(current)
        result = self.test_run["results"][row]
        self.current_result = result
        
        self.context_view.setText(result["context"])
        self.response_view.setText(result["modelResponse"])
        
        # Update validation button states
        validation = result.get("validation", {})
        if validation:
            # Set button styles based on current validation
            is_success = validation["status"]
            self.success_btn.setStyleSheet(
                "background-color: #90EE90;" if is_success else "background-color: none;"
            )
            self.fail_btn.setStyleSheet(
                "background-color: #FFB6C1;" if not is_success else "background-color: none;"
            )
        else:
            # Reset button styles
            self.success_btn.setStyleSheet("")
            self.fail_btn.setStyleSheet("")
    
    def validate_result(self, success: bool):
        """Record manual validation for the current result"""
        if self.current_result is None:
            return
        
        # Update validation
        self.current_result["validation"] = {
            "type": "manual",
            "status": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update list item
        current_item = self.results_list.currentItem()
        current_text = current_item.text().split()[0]  # Get "Result X" part
        current_item.setText(f"{current_text} {'✓' if success else '✗'}")
        
        # Update button styles
        self.success_btn.setStyleSheet(
            "background-color: #90EE90;" if success else "background-color: none;"
        )
        self.fail_btn.setStyleSheet(
            "background-color: #FFB6C1;" if not success else "background-color: none;"
        )
        
        # Move to next result if available
        self.show_next()
    
    def show_previous(self):
        """Show previous result"""
        current_row = self.results_list.currentRow()
        if current_row > 0:
            self.results_list.setCurrentRow(current_row - 1)
    
    def show_next(self):
        """Show next result"""
        current_row = self.results_list.currentRow()
        if current_row < self.results_list.count() - 1:
            self.results_list.setCurrentRow(current_row + 1)