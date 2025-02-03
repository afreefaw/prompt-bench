import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class TestRunner:
    def __init__(self, model: str = "llama3.2", url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.results_dir = Path("data/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    async def query_ollama_async(self, prompt: str, session: aiohttp.ClientSession) -> str:
        """Send an async request to the Ollama server"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with session.post(self.url, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("response", "No response received.")
        except Exception as e:
            return f"Error: {e}"
    
    async def process_contexts_async(self, prompt_text: str, contexts: List[str]) -> List[Dict]:
        """Process multiple contexts in parallel"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for context in contexts:
                full_prompt = f"{prompt_text}\n\nContext:\n{context}"
                task = asyncio.create_task(self.query_ollama_async(full_prompt, session))
                tasks.append((context, task))
            
            results = []
            for context, task in tasks:
                response = await task
                results.append({
                    "context": context,
                    "modelResponse": response,
                    "timestamp": datetime.now().isoformat()
                })
            
            return results
    
    def run_test(self, project_name: str, prompt_id: str, prompt_text: str,
                 contexts: List[str]) -> Dict:
        """Run a test with the given prompt and contexts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create and run event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run async processing
            results = loop.run_until_complete(
                self.process_contexts_async(prompt_text, contexts)
            )
        finally:
            loop.close()
        
        # Create test run data
        test_run = {
            "runId": f"run_{timestamp}",
            "projectName": project_name,
            "promptId": prompt_id,
            "promptText": prompt_text,
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
    
    def list_test_runs(self, project_name: str) -> List[Dict]:
        """List all test runs for a project with validation stats"""
        project_dir = self.results_dir / project_name
        if not project_dir.exists():
            return []
        
        runs = []
        for file_path in project_dir.glob("run_*.json"):
            try:
                with open(file_path) as f:
                    test_run = json.load(f)
                    # Calculate validation stats
                    total = len(test_run["results"])
                    # Calculate manual validation stats
                    manual_validated = sum(1 for r in test_run["results"]
                                        if "validations" in r and "manual" in r["validations"])
                    manual_success = sum(1 for r in test_run["results"]
                                      if "validations" in r and "manual" in r["validations"]
                                      and r["validations"]["manual"]["status"] is True)
                    manual_failed = sum(1 for r in test_run["results"]
                                     if "validations" in r and "manual" in r["validations"]
                                     and r["validations"]["manual"]["status"] is False)
                    manual_skipped = sum(1 for r in test_run["results"]
                                      if "validations" in r and "manual" in r["validations"]
                                      and r["validations"]["manual"]["status"] == "skipped")

                    # Calculate OpenAI validation stats
                    openai_validated = sum(1 for r in test_run["results"]
                                        if "validations" in r and "openai" in r["validations"])
                    openai_success = sum(1 for r in test_run["results"]
                                      if "validations" in r and "openai" in r["validations"]
                                      and r["validations"]["openai"]["status"] is True)
                    openai_failed = sum(1 for r in test_run["results"]
                                     if "validations" in r and "openai" in r["validations"]
                                     and r["validations"]["openai"]["status"] is False)
                    
                    runs.append({
                        "runId": test_run["runId"],
                        "timestamp": test_run["timestamp"],
                        "promptId": test_run["promptId"],
                        "stats": {
                            "total": total,
                            "total": total,
                            "manual": {
                                "validated": manual_validated,
                                "success": manual_success,
                                "failed": manual_failed,
                                "skipped": manual_skipped,
                                "progress": (manual_validated / total * 100) if total > 0 else 0,
                                "successRate": (manual_success / (manual_validated - manual_skipped) * 100)
                                             if (manual_validated - manual_skipped) > 0 else 0
                            },
                            "openai": {
                                "validated": openai_validated,
                                "success": openai_success,
                                "failed": openai_failed,
                                "progress": (openai_validated / total * 100) if total > 0 else 0,
                                "successRate": (openai_success / openai_validated * 100) if openai_validated > 0 else 0
                            }
                        }
                    })
            except Exception as e:
                print(f"Error loading test run {file_path}: {e}")
                continue
        
        # Sort by timestamp descending
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        return runs

    def save_validation(self, project_name: str, run_id: str, test_run: Dict):
        """Save validation results for a test run"""
        file_path = self.results_dir / project_name / f"{run_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Test run not found: {run_id}")
        
        with open(file_path, 'w') as f:
            json.dump(test_run, f, indent=2)

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