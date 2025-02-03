import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class Project:
    def __init__(self, name: str, created: Optional[str] = None):
        self.name = name
        self.created = created or datetime.now().isoformat()
        self.prompts: List[Dict] = []
        self.data_sources: List[Dict] = []

class ProjectManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.projects_file = self.data_dir / "projects.json"
        self.results_dir = self.data_dir / "results"
        self.init_directories()
    
    def init_directories(self):
        """Create necessary directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
    
    def load_projects(self) -> List[Project]:
        """Load all projects from the projects.json file"""
        if not self.projects_file.exists():
            return []
        
        try:
            with open(self.projects_file) as f:
                data = json.load(f)
                projects = []
                for project_data in data.get("projects", []):
                    project = Project(
                        name=project_data["name"],
                        created=project_data["created"]
                    )
                    project.prompts = project_data.get("prompts", [])
                    project.data_sources = project_data.get("dataSources", [])
                    projects.append(project)
                return projects
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []
    
    def save_projects(self, projects: List[Project]):
        """Save all projects to the projects.json file"""
        data = {
            "projects": [
                {
                    "name": project.name,
                    "created": project.created,
                    "prompts": project.prompts,
                    "dataSources": project.data_sources
                }
                for project in projects
            ]
        }
        
        try:
            with open(self.projects_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving projects: {e}")
    
    def create_project(self, name: str) -> Optional[Project]:
        """Create a new project with the given name"""
        # Check if project name already exists
        existing = self.load_projects()
        if any(p.name == name for p in existing):
            return None
        
        project = Project(name)
        existing.append(project)
        self.save_projects(existing)
        return project
    
    def add_prompt(self, project: Project, prompt_text: str):
        """Add a new prompt to the project"""
        prompt = {
            "id": f"prompt_{len(project.prompts) + 1}",
            "text": prompt_text,
            "created": datetime.now().isoformat()
        }
        project.prompts.append(prompt)
        self._save_project(project)
    
    def add_data_source(self, project: Project, file_path: str):
        """Add a data source to the project"""
        data_source = {
            "path": str(file_path),
            "type": Path(file_path).suffix[1:],  # Remove the dot
            "lastUsed": datetime.now().isoformat()
        }
        project.data_sources.append(data_source)
        self._save_project(project)
    
    def _save_project(self, project: Project):
        """Helper method to save a single project update"""
        projects = self.load_projects()
        for i, p in enumerate(projects):
            if p.name == project.name:
                projects[i] = project
                break
        self.save_projects(projects)
    
    def get_project(self, name: str) -> Optional[Project]:
        """Get a project by name"""
        projects = self.load_projects()
        for project in projects:
            if project.name == name:
                return project
        return None
    
    def _remove_project_results(self, project_name: str):
        """Remove all test results for a project"""
        project_results_dir = self.results_dir / project_name
        if project_results_dir.exists():
            # Remove all files in the directory
            for file in project_results_dir.glob("*"):
                file.unlink()
            # Remove the directory itself
            project_results_dir.rmdir()
    
    def delete_project(self, name: str) -> bool:
        """Delete a project by name"""
        projects = self.load_projects()
        initial_count = len(projects)
        projects = [p for p in projects if p.name != name]
        
        if len(projects) < initial_count:
            # Save updated projects list
            self.save_projects(projects)
            # Clean up project results
            self._remove_project_results(name)
            return True
        return False