from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt
import asyncio
from datetime import datetime
from typing import Dict, Optional

from openai_validator import OpenAIValidator

class BatchValidationDialog(QDialog):
    def __init__(self, test_run: Dict, project_name: str, test_runner, parent=None):
        super().__init__(parent)
        self.test_run = test_run
        self.project_name = project_name
        self.test_runner = test_runner
        
        try:
            self.openai_validator = OpenAIValidator()
            self.has_openai = True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"OpenAI validation not available: {str(e)}"
            )
            self.reject()
            return
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("OpenAI Batch Validation")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("OpenAI Batch Validation")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Count selection
        count_layout = QHBoxLayout()
        count_label = QLabel("Number of examples to validate:")
        self.count_spin = QSpinBox()
        
        # Calculate max examples (without OpenAI validation)
        self.unvalidated = len([
            r for r in self.test_run["results"]
            if "validations" not in r or "openai" not in r["validations"]
        ])
        
        # Set range and default value
        self.count_spin.setRange(1, self.unvalidated)
        default_count = min(100, self.unvalidated)
        self.count_spin.setValue(default_count)
        
        self.start_index = 0  # Default to start from beginning
        
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_spin)
        layout.addLayout(count_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Validation")
        self.run_btn.clicked.connect(self._run_validation)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def _run_validation(self):
        """Run the batch validation"""
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        
        count = self.count_spin.value()
        
        # Create and run event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats = loop.run_until_complete(self._validate_batch(count))
            
            # Show results
            QMessageBox.information(
                self,
                "Validation Complete",
                f"Validated {stats['validated']} examples:\n"
                f"Success Rate: {stats['success_rate']:.1f}%\n"
                f"✓ {stats['success']} successes\n"
                f"✗ {stats['failed']} failures"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Validation failed: {str(e)}"
            )
            self.reject()
        finally:
            loop.close()
    
    def set_count(self, count: int):
        """Set the number of examples to validate"""
        count = min(count, self.unvalidated)
        self.count_spin.setValue(count)
    
    def set_start_index(self, index: int):
        """Set the starting index for validation"""
        self.start_index = index
        
    async def _validate_batch(self, count: int) -> Dict:
        """Run batch validation and update progress"""
        def update_progress(validated: int, total: int):
            progress = (validated / total * 100)
            self.progress_bar.setValue(int(progress))
            self.progress_label.setText(
                f"Validating {validated}/{total} examples..."
            )
        
        # Create a modified test run starting from the specified index
        if self.start_index > 0:
            modified_test_run = self.test_run.copy()
            modified_test_run["results"] = self.test_run["results"][self.start_index:]
        else:
            modified_test_run = self.test_run
            
        # Run validation
        stats = await self.openai_validator.validate_batch(
            modified_test_run,
            count,
            update_progress
        )
        
        # Save results
        try:
            self.test_runner.save_validation(
                self.project_name,
                self.test_run["runId"],
                self.test_run
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save validation results: {str(e)}"
            )
        
        return stats