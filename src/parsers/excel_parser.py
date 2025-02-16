import pandas as pd
from pathlib import Path
from .base_parser import BaseParser

class ExcelParser(BaseParser):
    def parse(self, excel_path: str) -> list[str]:
        """
        Parse an Excel file, using the first column as context strings.
        
        Args:
            excel_path (str): Path to the Excel file
            
        Returns:
            list[str]: List of context strings from the first column
            
        Raises:
            ValueError: If the Excel file is empty or invalid
            FileNotFoundError: If the file does not exist
        """
        path = Path(excel_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {excel_path}")
            
        try:
            df = pd.read_excel(path)
            if df.empty:
                raise ValueError("Excel file is empty")
                
            # Use first column as contexts
            contexts = df.iloc[:, 0].astype(str).tolist()
            if not contexts:
                raise ValueError("No data found in first column")
                
            return contexts
            
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")