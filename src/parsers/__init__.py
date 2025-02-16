from .base_parser import BaseParser
from .json_parser import JSONParser
from .excel_parser import ExcelParser

__all__ = ['BaseParser', 'JSONParser', 'ExcelParser', 'discover_parsers']

def discover_parsers():
    """
    Returns a dictionary of available parsers.
    The key is the parser's display name, and the value is the parser instance.
    """
    return {
        'JSON': JSONParser(),
        'Excel': ExcelParser()
    }