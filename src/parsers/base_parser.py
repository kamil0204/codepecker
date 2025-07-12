"""
Base parser interface for language-specific parsers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    """Abstract base class for language parsers"""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a single file and extract classes and methods
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary containing parsed information
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
