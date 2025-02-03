from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QTextEdit, QLabel, QFileDialog,
    QMessageBox, QDialog, QInputDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime

from project_manager import Project
from test_runner import TestRunner, DataSourceHandler
from results_viewer import ResultsViewer

class TestResultsDialog(QDialog):
    def __init__(self, test_run, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Results")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        viewer = ResultsViewer(test_run)
        layout.addWidget(viewer)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class ProjectView(QWidget):
    def __init__(self, project: Project, project_manager, parent=None):
        super().__init__(parent)
        self.project = project
        self.project_manager = project_manager
        self.test_runner = TestRunner()
        self.setup_ui()
        self.load_project_data()
    
    def setup_ui(self):
        """Setup the project view UI"""
        layout = QVBoxLayout(self)
        
        # Project header
        header = QLabel(f"Project: {self.project.name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Main content area
        content = QHBoxLayout()
        
        # Left side - Prompts
        prompts_widget = QWidget()
        prompts_layout = QVBoxLayout(prompts_widget)
        
        prompts_header = QLabel("Prompts")
        prompts_header.setStyleSheet("font-weight: bold;")
        self.prompt_list = QListWidget()
        self.prompt_list.currentItemChanged.connect(self.on_prompt_selected)
        
        add_prompt_btn = QPushButton("Add Prompt")
        add_prompt_btn.clicked.connect(self.add_prompt)
        delete_prompt_btn = QPushButton("Delete Prompt")
        delete_prompt_btn.clicked.connect(self.delete_prompt)
        
        prompts_layout.addWidget(prompts_header)
        prompts_layout.addWidget(self.prompt_list)
        prompts_layout.addWidget(add_prompt_btn)
        prompts_layout.addWidget(delete_prompt_btn)
        
        # Right side - Prompt editor and data sources
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Prompt editor
        editor_header = QLabel("Prompt Text")
        editor_header.setStyleSheet("font-weight: bold;")
        self.prompt_editor = QTextEdit()
        self.prompt_editor.textChanged.connect(self.on_prompt_edited)
        
        # Data sources
        sources_header = QLabel("Data Sources")
        sources_header.setStyleSheet("font-weight: bold;")
        self.sources_list = QListWidget()
        
        add_source_btn = QPushButton("Add Data Source")
        add_source_btn.clicked.connect(self.add_data_source)
        
        editor_layout.addWidget(editor_header)
        editor_layout.addWidget(self.prompt_editor)
        editor_layout.addWidget(sources_header)
        editor_layout.addWidget(self.sources_list)
        editor_layout.addWidget(add_source_btn)
        
        # Add test controls
        test_layout = QHBoxLayout()
        run_test_btn = QPushButton("Run Test")
        run_test_btn.clicked.connect(self.run_test)
        view_results_btn = QPushButton("View Results")
        view_results_btn.clicked.connect(self.view_results)
        
        test_layout.addWidget(run_test_btn)
        test_layout.addWidget(view_results_btn)
        editor_layout.addLayout(test_layout)
        
        # Add widgets to content layout
        content.addWidget(prompts_widget, 1)
        content.addWidget(editor_widget, 2)
        
        layout.addLayout(content)
    
    def load_project_data(self):
        """Load project prompts and data sources"""
        # Load prompts
        self.prompt_list.clear()
        for prompt in self.project.prompts:
            self.prompt_list.addItem(prompt["text"][:50] + "...")
        
        # Load data sources
        self.sources_list.clear()
        for source in self.project.data_sources:
            self.sources_list.addItem(source["path"])
    
    def add_prompt(self):
        """Add a new prompt to the project"""
        self.project_manager.add_prompt(self.project, "New Prompt")
        self.load_project_data()
        # Select the new prompt
        self.prompt_list.setCurrentRow(self.prompt_list.count() - 1)
    
    def delete_prompt(self):
        """Delete the selected prompt"""
        current = self.prompt_list.currentRow()
        if current >= 0:
            reply = QMessageBox.question(
                self, "Delete Prompt",
                "Are you sure you want to delete this prompt?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.project.prompts.pop(current)
                self.project_manager._save_project(self.project)
                self.load_project_data()
    
    def on_prompt_selected(self, current, previous):
        """Handle prompt selection"""
        if current is None:
            self.prompt_editor.clear()
            return
        
        row = self.prompt_list.row(current)
        if 0 <= row < len(self.project.prompts):
            self.prompt_editor.setText(self.project.prompts[row]["text"])
    
    def on_prompt_edited(self):
        """Handle prompt text changes"""
        current = self.prompt_list.currentRow()
        if current >= 0:
            self.project.prompts[current]["text"] = self.prompt_editor.toPlainText()
            self.project_manager._save_project(self.project)
            # Update list item
            self.prompt_list.currentItem().setText(
                self.prompt_editor.toPlainText()[:50] + "..."
            )
    
    def add_data_source(self):
        """Add a new data source"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data Source",
            "",
            "JSON Files (*.json);;Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            try:
                # Validate the file can be loaded
                DataSourceHandler.load_contexts(file_path)
                self.project_manager.add_data_source(self.project, file_path)
                self.load_project_data()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load data source: {str(e)}"
                )
    
    def run_test(self):
        """Run test with current prompt and data source"""
        # Check if prompt is selected
        current_prompt = self.prompt_list.currentRow()
        if current_prompt < 0:
            QMessageBox.warning(self, "Error", "Please select a prompt")
            return
        
        # Check if data source is selected
        current_source = self.sources_list.currentRow()
        if current_source < 0:
            QMessageBox.warning(self, "Error", "Please select a data source")
            return
        
        prompt = self.project.prompts[current_prompt]
        data_source = self.project.data_sources[current_source]
        
        try:
            # Load contexts from data source
            contexts = DataSourceHandler.load_contexts(data_source["path"])
            
            # Run test
            test_run = self.test_runner.run_test(
                self.project.name,
                prompt["id"],
                prompt["text"],
                contexts
            )
            
            # Show results
            self.show_results_dialog(test_run)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Test failed: {str(e)}")
    
    def view_results(self):
        """View test results"""
        # Get list of test runs
        runs = self.test_runner.list_test_runs(self.project.name)
        if not runs:
            QMessageBox.information(self, "Info", "No test runs found")
            return
        
        # Show dialog to select run
        run_id, ok = QInputDialog.getItem(
            self,
            "Select Test Run",
            "Choose a test run to view:",
            runs,
            0,
            False
        )
        
        if ok and run_id:
            test_run = self.test_runner.load_results(self.project.name, run_id)
            if test_run:
                self.show_results_dialog(test_run)
            else:
                QMessageBox.critical(self, "Error", "Failed to load test results")
    
    def show_results_dialog(self, test_run):
        """Show the results dialog"""
        dialog = TestResultsDialog(test_run, self)
        dialog.exec_()