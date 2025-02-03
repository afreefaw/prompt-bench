from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QTextEdit, QLabel, QComboBox,
    QMessageBox, QSpinBox, QDialog, QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import Qt
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from openai_validator import OpenAIValidator
from validation_dialog import BatchValidationDialog

class TestRunsViewer(QWidget):
    def __init__(self, project_name: str, test_runner, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.test_runner = test_runner
        self.setup_ui()
        self.load_runs()
    
    def setup_ui(self):
        """Setup the test runs viewer UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Test Runs")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Test runs list
        self.runs_list = QListWidget()
        self.runs_list.itemDoubleClicked.connect(self.view_run)
        layout.addWidget(self.runs_list)
        
        # Controls
        controls = QHBoxLayout()
        
        view_btn = QPushButton("View Results")
        view_btn.clicked.connect(self.view_selected_run)
        validate_btn = QPushButton("🤖 Batch OpenAI Validate")
        validate_btn.clicked.connect(self.batch_validate_run)
        delete_btn = QPushButton("Delete Run")
        delete_btn.clicked.connect(self.delete_run)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_runs)
        
        controls.addWidget(view_btn)
        controls.addWidget(validate_btn)
        controls.addWidget(delete_btn)
        controls.addWidget(refresh_btn)
        layout.addLayout(controls)
    
    def load_runs(self):
        """Load test runs with validation stats"""
        self.runs_list.clear()
        runs = self.test_runner.list_test_runs(self.project_name)
        
        for run in runs:
            # Get stats
            stats = run["stats"]
            manual = stats["manual"]
            openai = stats["openai"]
            
            # Format timestamp
            timestamp = datetime.fromisoformat(run["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format manual stats
            manual_text = (f"Manual: {manual['validated']}/{stats['total']} ({manual['progress']:.1f}%) | "
                         f"Rate: {manual['successRate']:.1f}% | "
                         f"✓{manual['success']} ✗{manual['failed']} ⚪{manual['skipped']}")
            
            # Format OpenAI stats if any validations exist
            openai_text = ""
            if openai["validated"] > 0:
                openai_text = (f"\nOpenAI: {openai['validated']}/{stats['total']} ({openai['progress']:.1f}%) | "
                             f"Rate: {openai['successRate']:.1f}% | "
                             f"✓{openai['success']} ✗{openai['failed']}")
            
            # Combine stats
            stats_text = manual_text + openai_text
            
            item_text = f"{timestamp} - Run {run['runId']}\n{stats_text}"
            self.runs_list.addItem(item_text)
    
    def view_run(self, item):
        """View the selected test run"""
        run_id = self._get_run_id_from_item(item)
        if run_id:
            test_run = self.test_runner.load_results(self.project_name, run_id)
            if test_run:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Test Results - {run_id}")
                dialog.resize(1600, 1000)
                layout = QVBoxLayout(dialog)
                viewer = ResultsViewer(test_run, self.project_name, self.test_runner, dialog)
                layout.addWidget(viewer)
                dialog.exec_()
                # Refresh list after viewing to update stats
                self.load_runs()
    
    def view_selected_run(self):
        """View the selected test run"""
        current = self.runs_list.currentItem()
        if current:
            self.view_run(current)
        else:
            QMessageBox.warning(self, "Error", "Please select a test run to view")
    
    def delete_run(self):
        """Delete the selected test run"""
        current = self.runs_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a test run to delete")
            return
        
        run_id = self._get_run_id_from_item(current)
        if run_id:
            reply = QMessageBox.question(
                self,
                "Delete Test Run",
                f"Are you sure you want to delete test run {run_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Delete the test run file
                    file_path = self.test_runner.results_dir / self.project_name / f"{run_id}.json"
                    if file_path.exists():
                        file_path.unlink()
                        self.load_runs()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to delete test run: {str(e)}"
                    )
    
    def batch_validate_run(self):
        """Run batch OpenAI validation on the selected test run"""
        current = self.runs_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a test run to validate")
            return
        
        run_id = self._get_run_id_from_item(current)
        if run_id:
            test_run = self.test_runner.load_results(self.project_name, run_id)
            if test_run:
                # Load project to get prompt text
                projects_file = Path("data/projects.json")
                try:
                    with open(projects_file) as f:
                        projects_data = json.load(f)
                        # Find project and prompt
                        project = next((p for p in projects_data["projects"]
                                     if p["name"] == self.project_name), None)
                        if not project:
                            raise ValueError(f"Project {self.project_name} not found")
                        prompt = next((p for p in project["prompts"]
                                    if p["id"] == test_run["promptId"]), None)
                        if prompt:
                            test_run["promptText"] = prompt["text"]
                            dialog = BatchValidationDialog(test_run, self.project_name, self.test_runner, self)
                            if dialog.exec_() == QDialog.Accepted:
                                # Refresh list to show updated stats
                                self.load_runs()
                        else:
                            QMessageBox.critical(self, "Error", "Could not find prompt text for this test run")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load prompt text: {str(e)}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load test results")
    
    def _get_run_id_from_item(self, item) -> Optional[str]:
        """Extract run ID from list item text"""
        text = item.text()
        try:
            # Text format: "YYYY-MM-DD HH:MM:SS - Run run_YYYYMMDD_HHMMSS"
            return text.split(" - Run ")[1].split("\n")[0]
        except:
            return None


class ResultsViewer(QWidget):
    def __init__(self, test_run: Dict, project_name: str, test_runner, parent=None):
        super().__init__(parent)
        self.test_run = test_run
        self.project_name = project_name
        self.test_runner = test_runner
        self.current_result = None
        try:
            self.openai_validator = OpenAIValidator()
            self.has_openai = True
        except Exception as e:
            print(f"OpenAI validation not available: {e}")
            self.has_openai = False
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
        right_layout.addWidget(QLabel("Ollama Model Response:"))
        self.response_view = QTextEdit()
        self.response_view.setReadOnly(True)
        right_layout.addWidget(self.response_view)
        
        # OpenAI response
        right_layout.addWidget(QLabel("OpenAI Response:"))
        self.openai_response_view = QTextEdit()
        self.openai_response_view.setReadOnly(True)
        right_layout.addWidget(self.openai_response_view)
        
        # OpenAI validation options
        openai_options = QHBoxLayout()
        self.strip_whitespace = QCheckBox("Strip Whitespace")
        self.strip_whitespace.setChecked(True)
        self.strip_whitespace.stateChanged.connect(self._update_openai_validation)
        self.strip_punctuation = QCheckBox("Strip Punctuation")
        self.strip_punctuation.setChecked(True)
        self.strip_punctuation.stateChanged.connect(self._update_openai_validation)
        openai_options.addWidget(self.strip_whitespace)
        openai_options.addWidget(self.strip_punctuation)
        right_layout.addLayout(openai_options)
        
        # Validation controls
        validation_layout = QHBoxLayout()
        
        # Manual validation
        manual_group = QGroupBox("Manual Validation")
        manual_layout = QHBoxLayout()
        self.success_btn = QPushButton("✓ Success")
        self.success_btn.clicked.connect(lambda: self.validate_result(True))
        self.fail_btn = QPushButton("✗ Fail")
        self.fail_btn.clicked.connect(lambda: self.validate_result(False))
        manual_layout.addWidget(self.success_btn)
        manual_layout.addWidget(self.fail_btn)
        manual_group.setLayout(manual_layout)
        
        # OpenAI validation
        openai_group = QGroupBox("OpenAI Validation")
        openai_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.openai_btn = QPushButton("🤖 Validate Current")
        self.openai_btn.clicked.connect(self._run_openai_validation)
        self.openai_btn.setEnabled(self.has_openai)
        
        self.openai_batch_btn = QPushButton("🤖 Batch Validate All")
        self.openai_batch_btn.clicked.connect(self._run_openai_batch_validation)
        self.openai_batch_btn.setEnabled(self.has_openai)
        
        if not self.has_openai:
            tooltip = "OpenAI validation not available. Check your API key configuration."
            self.openai_btn.setToolTip(tooltip)
            self.openai_batch_btn.setToolTip(tooltip)
            
        buttons_layout.addWidget(self.openai_btn)
        buttons_layout.addWidget(self.openai_batch_btn)
        openai_layout.addLayout(buttons_layout)
        openai_group.setLayout(openai_layout)
        
        validation_layout.addWidget(manual_group)
        validation_layout.addWidget(openai_group)
        right_layout.addLayout(validation_layout)
        
        # Progress tracking
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("Progress: 0/0 (0%)")
        progress_layout.addWidget(self.progress_label)
        right_layout.addLayout(progress_layout)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.show_previous)
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.show_next)
        self.random_btn = QPushButton("Random")
        self.random_btn.clicked.connect(self.show_random)
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.skip_result)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.random_btn)
        nav_layout.addWidget(self.skip_btn)
        right_layout.addLayout(nav_layout)
        
        # Add panels to content layout
        content.addWidget(left_panel, 1)
        content.addWidget(right_panel, 2)
        layout.addLayout(content)
    
    def load_results(self):
        """Load results into the list widget"""
        self.results_list.clear()
        for i, result in enumerate(self.test_run["results"], 1):
            # Build status indicators
            manual_status = ""
            openai_status = ""
            
            if "validations" in result:
                if "manual" in result["validations"]:
                    manual = result["validations"]["manual"]
                    if manual["status"] == "skipped":
                        manual_status = "⚪"
                    else:
                        manual_status = "✓" if manual["status"] else "✗"
                
                if "openai" in result["validations"]:
                    openai = result["validations"]["openai"]
                    openai_status = "✓" if openai["status"] else "✗"
            
            status_text = ""
            if manual_status:
                status_text += f" M:{manual_status}"
            if openai_status:
                status_text += f" AI:{openai_status}"
            
            self.results_list.addItem(f"Result {i}{status_text}")
        
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
        
        self.update_progress()
    
    def on_result_selected(self, current, previous):
        """Handle result selection"""
        if current is None:
            return
        
        row = self.results_list.row(current)
        result = self.test_run["results"][row]
        self.current_result = result
        
        # Display context and responses
        self.context_view.setText(result["context"])
        self.response_view.setText(result["modelResponse"])
        
        # Display OpenAI response if available
        if "validations" in result and "openai" in result["validations"]:
            openai_validation = result["validations"]["openai"]
            self.openai_response_view.setText(openai_validation.get("response", ""))
        else:
            self.openai_response_view.clear()
        
        # Update validation button states
        validations = result.get("validations", {})
        
        # Manual validation state
        manual = validations.get("manual", {})
        if manual:
            is_success = manual["status"]
            self.success_btn.setStyleSheet(
                "background-color: #90EE90;" if is_success else "background-color: none;"
            )
            self.fail_btn.setStyleSheet(
                "background-color: #FFB6C1;" if not is_success else "background-color: none;"
            )
        else:
            self.success_btn.setStyleSheet("")
            self.fail_btn.setStyleSheet("")
    
    def validate_result(self, success: bool):
        """Record manual validation for the current result"""
        if self.current_result is None:
            return
        
        # Update manual validation
        if "validations" not in self.current_result:
            self.current_result["validations"] = {}
        
        self.current_result["validations"]["manual"] = {
            "status": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save validation results
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
                f"Failed to save validation: {str(e)}"
            )
            return
        
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
        
        # Update progress tracking
        self.update_progress()
        
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
    
    def show_random(self):
        """Show a random unvalidated result"""
        import random
        unvalidated = [
            i for i, result in enumerate(self.test_run["results"])
            if "validations" not in result or "manual" not in result["validations"]
        ]
        if unvalidated:
            self.results_list.setCurrentRow(random.choice(unvalidated))
    
    def skip_result(self):
        """Skip the current result"""
        if self.current_result is None:
            return
        
        # Mark as skipped in manual validation
        if "validations" not in self.current_result:
            self.current_result["validations"] = {}
        
        self.current_result["validations"]["manual"] = {
            "status": "skipped",
            "timestamp": datetime.now().isoformat()
        }
        
        # Update list item
        current_item = self.results_list.currentItem()
        current_text = current_item.text().split()[0]  # Get "Result X" part
        current_item.setText(f"{current_text} ⚪")  # Use circle for skipped
        
        # Reset button styles
        self.success_btn.setStyleSheet("")
        self.fail_btn.setStyleSheet("")
        
        # Update progress and move to next
        self.update_progress()
        self.show_next()
    
    def _run_openai_validation(self):
        """Run OpenAI validation for current result"""
        if not self.has_openai or self.current_result is None:
            return
        
        dialog = BatchValidationDialog(self.test_run, self.project_name, self.test_runner, self)
        dialog.set_count(1)  # Validate only current result
        dialog.set_start_index(self.results_list.currentRow())
        if dialog.exec_() == QDialog.Accepted:
            self.load_results()  # Refresh the display
            
    def _run_openai_batch_validation(self):
        """Run OpenAI validation for all results"""
        if not self.has_openai:
            return
            
        dialog = BatchValidationDialog(self.test_run, self.project_name, self.test_runner, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_results()  # Refresh the display

    def _update_openai_validation(self):
        """Update OpenAI validation based on stripping options"""
        if not self.current_result or "validations" not in self.current_result or "openai" not in self.current_result["validations"]:
            return
            
        openai_validation = self.current_result["validations"]["openai"]
        model_response = self.current_result["modelResponse"]
        openai_response = openai_validation.get("response", "")
        
        # Apply stripping options
        if self.strip_whitespace.isChecked():
            model_response = ''.join(model_response.split())
            openai_response = ''.join(openai_response.split())
            
        if self.strip_punctuation.isChecked():
            import string
            translator = str.maketrans('', '', string.punctuation)
            model_response = model_response.translate(translator)
            openai_response = openai_response.translate(translator)
        
        # Convert to lowercase for case-insensitive comparison
        model_response = model_response.lower()
        openai_response = openai_response.lower()
        
        # Update validation status
        openai_validation["status"] = model_response == openai_response
        
        # Save the updated validation
        try:
            self.test_runner.save_validation(
                self.project_name,
                self.test_run["runId"],
                self.test_run
            )
            
            # Update list item
            current_item = self.results_list.currentItem()
            if current_item:
                row = self.results_list.row(current_item)
                result = self.test_run["results"][row]
                
                # Build status text
                manual_status = ""
                openai_status = ""
                
                if "validations" in result:
                    if "manual" in result["validations"]:
                        manual = result["validations"]["manual"]
                        if manual["status"] == "skipped":
                            manual_status = "⚪"
                        else:
                            manual_status = "✓" if manual["status"] else "✗"
                    
                    if "openai" in result["validations"]:
                        openai = result["validations"]["openai"]
                        openai_status = "✓" if openai["status"] else "✗"
                
                status_text = ""
                if manual_status:
                    status_text += f" M:{manual_status}"
                if openai_status:
                    status_text += f" AI:{openai_status}"
                
                current_item.setText(f"Result {row + 1}{status_text}")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save validation: {str(e)}"
            )

    def update_progress(self):
        """Update progress tracking"""
        total = len(self.test_run["results"])
        
        # Manual validation stats
        manual_validated = sum(1 for r in self.test_run["results"]
                             if "validations" in r and "manual" in r["validations"])
        manual_success = sum(1 for r in self.test_run["results"]
                           if "validations" in r and "manual" in r["validations"]
                           and r["validations"]["manual"]["status"] is True)
        manual_failed = sum(1 for r in self.test_run["results"]
                          if "validations" in r and "manual" in r["validations"]
                          and r["validations"]["manual"]["status"] is False)
        manual_skipped = sum(1 for r in self.test_run["results"]
                           if "validations" in r and "manual" in r["validations"]
                           and r["validations"]["manual"]["status"] == "skipped")
        
        # OpenAI validation stats
        openai_validated = sum(1 for r in self.test_run["results"]
                             if "validations" in r and "openai" in r["validations"])
        openai_success = sum(1 for r in self.test_run["results"]
                           if "validations" in r and "openai" in r["validations"]
                           and r["validations"]["openai"]["status"] is True)
        openai_failed = sum(1 for r in self.test_run["results"]
                          if "validations" in r and "openai" in r["validations"]
                          and r["validations"]["openai"]["status"] is False)
        
        # Calculate progress percentages
        manual_progress = (manual_validated / total * 100) if total > 0 else 0
        openai_progress = (openai_validated / total * 100) if total > 0 else 0
        
        # Format progress text
        progress_text = f"Manual: {manual_validated}/{total} ({manual_progress:.1f}%) | "
        progress_text += f"✓ {manual_success} | ✗ {manual_failed} | ⚪ {manual_skipped}\n"
        if openai_validated > 0:
            progress_text += f"OpenAI: {openai_validated}/{total} ({openai_progress:.1f}%) | "
            progress_text += f"✓ {openai_success} | ✗ {openai_failed}"
        
        self.progress_label.setText(progress_text)