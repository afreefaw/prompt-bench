import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import requests

class TestRunner:
    def __init__(self, model: str = "llama3.2", url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.results_dir = Path("data/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def query_ollama(self, prompt: str) -> str:
        """Send a request to the Ollama server"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=data)
            response.raise_for_status()
            return response.json().get("response", "No response received.")
        except requests.exceptions.RequestException as e:
            return f"Error: {e}"
    
    def run_test(self, project_name: str, prompt_id: str, prompt_text: str, 
                 contexts: List[str]) -> Dict:
        """Run a test with the given prompt and contexts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = []
        
        for context in contexts:
            # Combine prompt and context
            full_prompt = f"{prompt_text}\n\nContext:\n{context}"
            
            # Get model response
            response = self.query_ollama(full_prompt)
            
            # Store result
            results.append({
                "context": context,
                "modelResponse": response,
                "timestamp": datetime.now().isoformat()
            })
        
        # Create test run data
        test_run = {
            "runId": f"run_{timestamp}",
            "projectName": project_name,
            "promptId": prompt_id,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        # Save results
        self.save_results(test_run)
        
        return test_run
    
    def save_results(self, test_run: Dict):
        """Save test results to a JSON file"""
        project_dir = self.results_dir / test_run["projectName"]
        project_dir.mkdir(exist_ok=True)
        
        file_path = project_dir / f"{test_run['runId']}.json"
        with open(file_path, 'w') as f:
            json.dump(test_run, f, indent=2)
    
    def load_results(self, project_name: str, run_id: str) -> Optional[Dict]:
        """Load test results from a JSON file"""
        file_path = self.results_dir / project_name / f"{run_id}.json"
        if not file_path.exists():
            return None
        
        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading results: {e}")
            return None
    
    def list_test_runs(self, project_name: str) -> List[str]:
        """List all test runs for a project"""
        project_dir = self.results_dir / project_name
        if not project_dir.exists():
            return []
        
        return [f.stem for f in project_dir.glob("run_*.json")]

class DataSourceHandler:
    """
    Handles loading and parsing of data source files.
    
    Expected JSON format:
    {
        "contexts": [
            "Context text 1",
            "Context text 2",
            ...
        ]
    }
    
    For Excel files:
    - First column is assumed to contain the context text
    """
    
    @staticmethod
    def load_contexts(file_path: str) -> List[str]:
        """Load contexts from a data source file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Data source not found: {file_path}")
        
        if path.suffix.lower() == '.json':
            return DataSourceHandler._load_json(path)
        elif path.suffix.lower() in ['.xlsx', '.xls']:
            return DataSourceHandler._load_excel(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")
    
    @staticmethod
    def _load_json(path: Path) -> List[str]:
        """Load contexts from a JSON file"""
        with open(path) as f:
            data = json.load(f)
            
            if not isinstance(data, dict) or "contexts" not in data:
                raise ValueError(
                    'Invalid JSON format. Expected: {"contexts": ["text1", "text2", ...]}'
                )
            
            contexts = data["contexts"]
            if not isinstance(contexts, list) or not all(isinstance(c, str) for c in contexts):
                raise ValueError("The 'contexts' field must be an array of strings")
            
            return contexts
    
    @staticmethod
    def _load_excel(path: Path) -> List[str]:
        """Load contexts from an Excel file"""
        import pandas as pd
        df = pd.read_excel(path)
        if df.empty:
            raise ValueError("Excel file is empty")
        # Use first column as contexts
        return df.iloc[:, 0].astype(str).tolist()