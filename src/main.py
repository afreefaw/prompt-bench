import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QPushButton, QStackedWidget,
    QMessageBox, QLabel
)
from PyQt5.QtCore import Qt

from project_manager import ProjectManager, Project
from dialogs import CreateProjectDialog
from views import ProjectView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama QA Testing GUI")
        self.setMinimumSize(1000, 600)
        
        # Initialize project manager
        self.project_manager = ProjectManager()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Left panel - Project list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Project list
        projects_label = QLabel("Projects")
        projects_label.setStyleSheet("font-weight: bold;")
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self.on_project_selected)
        create_project_btn = QPushButton("Create New Project")
        create_project_btn.clicked.connect(self.create_project)
        
        left_layout.addWidget(projects_label)
        left_layout.addWidget(create_project_btn)
        left_layout.addWidget(self.project_list)
        
        # Right panel - Stacked widget for different views
        self.right_panel = QStackedWidget()
        
        # Add welcome widget
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_label = QLabel("Welcome to Ollama QA Testing GUI\n\nSelect a project or create a new one to begin.")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.right_panel.addWidget(welcome_widget)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.right_panel, 3)
        
        # Load existing projects
        self.load_projects()
    
    def load_projects(self):
        """Load existing projects into the list widget"""
        self.project_list.clear()
        projects = self.project_manager.load_projects()
        for project in projects:
            self.project_list.addItem(project.name)
    
    def create_project(self):
        """Handle creating a new project"""
        dialog = CreateProjectDialog(self)
        if dialog.exec_():
            project_name = dialog.get_project_name()
            if not project_name:
                QMessageBox.warning(self, "Error", "Project name cannot be empty")
                return
            
            project = self.project_manager.create_project(project_name)
            if project is None:
                QMessageBox.warning(
                    self, "Error",
                    f"A project named '{project_name}' already exists"
                )
                return
            
            # Refresh project list
            self.load_projects()
            
            # Select the new project
            items = self.project_list.findItems(project_name, Qt.MatchExactly)
            if items:
                self.project_list.setCurrentItem(items[0])
    
    def on_project_selected(self, current, previous):
        """Handle project selection"""
        # Clear any existing widgets except the welcome widget
        while self.right_panel.count() > 1:
            widget = self.right_panel.widget(self.right_panel.count() - 1)
            self.right_panel.removeWidget(widget)
            widget.deleteLater()
        
        if current is None:
            self.right_panel.setCurrentIndex(0)  # Show welcome widget
            return
        
        project = self.project_manager.get_project(current.text())
        if project:
            # Create and show project view
            project_view = ProjectView(project, self.project_manager)
            self.right_panel.addWidget(project_view)
            self.right_panel.setCurrentWidget(project_view)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()