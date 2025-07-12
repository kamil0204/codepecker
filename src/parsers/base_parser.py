"""
Base parser interface for language-specific parsers.
Different languages may have different graph structures:
- C#/Java: Class-method graphs with method call relationships
- Python: Module-function graphs or class-method graphs depending on code structure
- JavaScript: Module-function graphs or prototype-based relationships
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    """Abstract base class for language parsers"""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a single file and extract structural elements.
        The structure may vary by language:
        - Object-oriented languages (C#, Java): classes and methods
        - Functional languages: modules and functions
        - Mixed paradigm languages (Python, JavaScript): flexible structure
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary containing parsed information with language-appropriate structure
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions supported by this parser
        
        Returns:
            List of file extensions (e.g., ['.cs', '.csx'])
        """
        pass
    
    def parse_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Parse multiple files
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            Dictionary mapping file paths to parsed information
        """
        results = {}
        for file_path in file_paths:
            try:
                results[file_path] = self.parse_file(file_path)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                results[file_path] = {"error": str(e)}
        return results
