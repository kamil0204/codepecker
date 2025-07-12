"""
Parser manager for handling multiple language parsers.
Each parser generates language-appropriate graph structures:
- C# parser: Class-method graphs with method call relationships
- Future parsers may use different structures based on language paradigms
"""
import os
from typing import List, Dict, Any
from .base_parser import BaseParser
from .csharp_parser import CSharpParser


class ParserManager:
    """Manages multiple language parsers"""
    
    def __init__(self):
        self.parsers = {
            'csharp': CSharpParser(),  # Generates class-method graphs
            # Add more parsers here for other languages with appropriate structures:
            # 'python': PythonParser(),  # Could generate module-function or class-method graphs
            # 'java': JavaParser(),      # Would generate class-method graphs like C#
            # 'javascript': JSParser(),  # Could generate module-function or prototype graphs
        }
    
    def group_files_by_language(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Group file paths by programming language based on file extensions
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping language names to lists of file paths
        """
        grouped_files = {}
        
        for parser_name, parser in self.parsers.items():
            supported_extensions = parser.get_supported_extensions()
            matching_files = [
                path for path in file_paths 
                if any(path.lower().endswith(ext.lower()) for ext in supported_extensions)
            ]
            if matching_files:
                grouped_files[parser_name] = matching_files
        
        return grouped_files
    
    def parse_files_by_language(self, grouped_files: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        Parse files using appropriate language parsers
        
        Args:
            grouped_files: Dictionary mapping language names to file paths
            
        Returns:
            Dictionary mapping language names to parsing results
        """
        results = {}
        
        for language, file_paths in grouped_files.items():
            if language in self.parsers:
                parser = self.parsers[language]
                results[language] = parser.parse_files(file_paths)
            else:
                print(f"No parser available for language: {language}")
        
        return results
    
    def extract_files_from_entrypoints(self, entrypoints: List[Dict[str, Any]], project_path: str = None) -> List[str]:
        """
        Extract unique file paths from entrypoints list
        
        Args:
            entrypoints: List of entrypoint dictionaries
            project_path: Base project path to resolve relative paths
            
        Returns:
            List of unique file paths (absolute if project_path provided)
        """
        files = []
        for entry in entrypoints:
            if 'file' in entry and entry['file']:
                file_path = entry['file']
                
                # Convert relative paths to absolute paths if project_path is provided
                if project_path and not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                # Normalize the path to use OS-appropriate separators
                file_path = os.path.normpath(file_path)
                
                files.append(file_path)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(files))
    
    def print_parsing_results(self, results: Dict[str, Dict[str, Any]]):
        """
        Print parsing results in the specified format
        
        Args:
            results: Dictionary mapping language names to parsing results
        """
        for language, language_results in results.items():
            print(f"\n=== {language.upper()} FILES ===")
            
            for file_path, file_result in language_results.items():
                if 'error' in file_result:
                    print(f"\nError parsing {file_path}: {file_result['error']}")
                    continue
                
                print(f"\n<ClassNames> {file_path}")
                
                if 'classes' in file_result:
                    for class_info in file_result['classes']:
                        print(f"    {class_info['name']}")
                        
                        for method_info in class_info['methods']:
                            visibility = method_info.get('visibility', 'private')
                            print(f"        {method_info['name']} ({visibility})")
                
                if not file_result.get('classes'):
                    print("    No classes found")
