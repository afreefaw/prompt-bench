import json
from pathlib import Path
from .base_parser import BaseParser

class JSONParser(BaseParser):
    def parse(self, json_path: str) -> list[str]:
        """
        Parse a JSON file that contains either:
        1. A "contexts" array of strings
        2. A "documents" array with objects containing "content" fields
        
        Args:
            json_path (str): Path to the JSON file
            
        Returns:
            list[str]: List of context strings for testing
            
        Raises:
            ValueError: If the JSON format is invalid
            FileNotFoundError: If the file does not exist
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {json_path}")
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                raise ValueError("JSON root must be an object")
                
            # Try "contexts" format first
            if "contexts" in data:
                contexts = data["contexts"]
                if not isinstance(contexts, list):
                    raise ValueError("'contexts' must be an array")
                if not all(isinstance(c, str) for c in contexts):
                    raise ValueError("All items in 'contexts' must be strings")
                return contexts
                
            # Try "documents" format
            if "documents" in data:
                documents = data["documents"]
                if not isinstance(documents, list):
                    raise ValueError("'documents' must be an array")
                    
                contents = []
                for i, doc in enumerate(documents):
                    if not isinstance(doc, dict):
                        raise ValueError(f"Document at index {i} must be an object")
                    if "content" not in doc:
                        raise ValueError(f"Document at index {i} missing 'content' field")
                    if not isinstance(doc["content"], str):
                        raise ValueError(f"'content' field at index {i} must be a string")
                    contents.append(doc["content"])
                return contents
                
            raise ValueError(
                'Invalid JSON format. Expected either:\n'
                '{"contexts": ["text1", "text2", ...]} or\n'
                '{"documents": [{"content": "text1"}, {"content": "text2"}, ...]}'
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON syntax: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {str(e)}")