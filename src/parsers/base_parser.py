from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, input_source: str) -> list[str]:
        """
        Parse the input source and return a list of context strings.
        
        Args:
            input_source (str): Path to the file to parse
            
        Returns:
            list[str]: List of context strings that will be used for testing.
                      Each string represents one context that will be tested.
        
        Raises:
            ValueError: If the input source is invalid or cannot be parsed
            FileNotFoundError: If the input file does not exist
        """
        pass

    @property
    def name(self):
        """Return a human-readable name for this parser"""
        return self.__class__.__name__.replace('Parser', '')