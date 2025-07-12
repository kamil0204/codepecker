"""
C# parser using tree-sitter for building class-method graphs
"""
import os
from typing import List, Dict, Any
import tree_sitter_c_sharp as tscsharp
from tree_sitter import Language, Parser
from .base_parser import BaseParser


class CSharpParser(BaseParser):
    """C# parser implementation for generating class-method graphs using tree-sitter"""
    
    def __init__(self):
        self.language = Language(tscsharp.language())
        self.parser = Parser()
        self.parser.language = self.language
    
    def get_supported_extensions(self) -> List[str]:
        """Get C# file extensions"""
        return ['.cs', '.csx']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a C# file and extract classes and methods for class-method graph generation
        
        Args:
            file_path: Path to the C# file
            
        Returns:
            Dictionary containing classes and their methods with method call relationships
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:  # Use utf-8-sig to handle BOM
            content = f.read()
        
        tree = self.parser.parse(content.encode('utf-8'))
        root_node = tree.root_node
        
        result = {
            "file_path": file_path,
            "classes": []
        }
        
        # Find all class declarations
        classes = self._find_classes(root_node, content)
        result["classes"] = classes
        
        return result
    
    def _find_classes(self, node, content: str) -> List[Dict[str, Any]]:
        """Find all class declarations in the syntax tree"""
        classes = []
        
        # Look for class declarations
        if node.type == 'class_declaration':
            class_info = self._extract_class_info(node, content)
            if class_info:
                classes.append(class_info)
        
        # Recursively search child nodes
        for child in node.children:
            classes.extend(self._find_classes(child, content))
        
        return classes
    
    def _extract_class_info(self, class_node, content: str) -> Dict[str, Any]:
        """Extract class name and methods from a class declaration node"""
        class_name = None
        class_visibility = "private"  # Default visibility
        methods = []
        
        # Find class visibility and name
        found_class_keyword = False
        for child in class_node.children:
            child_text = content[child.start_byte:child.end_byte].strip()
            
            # Check for visibility modifiers
            if child_text in ['public', 'private', 'protected', 'internal']:
                class_visibility = child_text
            elif child.type == 'class' or child_text == 'class':
                found_class_keyword = True
            elif child.type == 'identifier' and found_class_keyword:
                class_name = child_text
                break
            elif child.type == 'identifier' and not found_class_keyword:
                # Sometimes the identifier comes before we see the 'class' keyword
                # Check if this looks like a class name (starts with uppercase)
                if child_text and child_text[0].isupper() and child_text not in ['public', 'private', 'protected', 'internal', 'static', 'abstract', 'sealed', 'partial']:
                    class_name = child_text
        
        if not class_name:
            # Fallback: look for any identifier that could be a class name
            for child in class_node.children:
                if child.type == 'identifier':
                    potential_name = content[child.start_byte:child.end_byte].strip()
                    if potential_name and potential_name[0].isupper():
                        class_name = potential_name
                        break
        
        if not class_name:
            return None
        
        # Find class body
        class_body = None
        for child in class_node.children:
            if child.type == 'declaration_list':
                class_body = child
                break
        
        if class_body:
            methods = self._find_methods(class_body, content)
        
        return {
            "name": class_name,
            "visibility": class_visibility,
            "methods": methods
        }
    
    def _find_methods(self, node, content: str) -> List[Dict[str, Any]]:
        """Find all method declarations in a class body"""
        methods = []
        
        # Look for method declarations
        if node.type == 'method_declaration':
            method_info = self._extract_method_info(node, content)
            if method_info:
                methods.append(method_info)
        
        # Recursively search child nodes
        for child in node.children:
            methods.extend(self._find_methods(child, content))
        
        return methods
    
    def _extract_method_info(self, method_node, content: str) -> Dict[str, Any]:
        """Extract method information from a method declaration node"""
        method_name = None
        visibility = "public"  # Default to public for controllers (most common)
        
        # Debug: Print the node structure
        # print(f"Method node type: {method_node.type}")
        # for i, child in enumerate(method_node.children):
        #     child_text = content[child.start_byte:child.end_byte]
        #     print(f"  Child {i}: {child.type} = '{child_text}'")
        
        # Look for modifiers first
        modifiers = []
        for child in method_node.children:
            child_text = content[child.start_byte:child.end_byte].strip()
            if child.type in ['modifier', 'modifiers'] or child_text in ['public', 'private', 'protected', 'internal', 'static', 'async', 'virtual', 'override']:
                modifiers.append(child_text)
                if child_text in ['public', 'private', 'protected', 'internal']:
                    visibility = child_text
        
        # Find the method name - it's usually an identifier that comes after modifiers and return type
        identifiers = []
        for child in method_node.children:
            if child.type == 'identifier':
                identifier_text = content[child.start_byte:child.end_byte]
                identifiers.append(identifier_text)
        
        # The method name is typically the last identifier before the parameter list
        # or the first identifier that's not a type name
        if identifiers:
            # Skip common type names and find the actual method name
            type_keywords = {'void', 'int', 'string', 'bool', 'Task', 'ActionResult', 'IActionResult', 'async', 'static'}
            for identifier in identifiers:
                if identifier not in type_keywords and not identifier.startswith('I') and identifier[0].isupper():
                    method_name = identifier
                    break
            
            # If we still don't have a method name, take the last identifier
            if not method_name and identifiers:
                method_name = identifiers[-1]
        
        if not method_name:
            return None
        
        # Find method calls within this method
        method_calls = self._find_method_calls_in_method(method_node, content)
        
        return {
            "name": method_name,
            "visibility": visibility,
            "method_calls": method_calls
        }
    
    def _find_method_calls_in_method(self, method_node, content: str) -> List[str]:
        """
        Find all method calls within a method body using a generic approach.
        This is specifically designed for C# class-method graph generation.
        For other languages (like Python), different approaches may be needed.
        """
        method_calls = []
        
        def traverse_for_calls(node):
            """Recursively traverse the tree to find method calls"""
            # Look for different types of method call patterns
            if node.type in ['invocation_expression', 'method_invocation', 'call_expression']:
                # Extract the method name from the invocation
                call_name = self._extract_call_name_from_invocation(node, content)
                if call_name and call_name not in method_calls:
                    method_calls.append(call_name)
            
            # Also look for member access expressions that might be method calls
            elif node.type == 'member_access_expression':
                # Check if this member access is part of an invocation
                parent = node.parent
                if parent and parent.type in ['invocation_expression', 'method_invocation', 'call_expression']:
                    call_name = self._extract_method_name_from_member_access(node, content)
                    if call_name and call_name not in method_calls:
                        method_calls.append(call_name)
            
            # Continue traversing children
            for child in node.children:
                traverse_for_calls(child)
        
        # Start traversal from the method node
        traverse_for_calls(method_node)
        
        return method_calls
    
    def _extract_call_name_from_invocation(self, invocation_node, content: str) -> str:
        """Extract method name from an invocation expression"""
        # Look for the method name in the invocation
        for child in invocation_node.children:
            if child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
            elif child.type == 'member_access_expression':
                # For method calls like obj.Method(), get the last identifier
                return self._extract_method_name_from_member_access(child, content)
        
        return None
    
    def _extract_method_name_from_member_access(self, member_access_node, content: str) -> str:
        """Extract method name from member access expression (e.g., obj.Method)"""
        # The method name is typically the last identifier in a member access
        identifiers = []
        for child in member_access_node.children:
            if child.type == 'identifier':
                identifiers.append(content[child.start_byte:child.end_byte])
        
        # Return the last identifier (the method name)
        if identifiers:
            return identifiers[-1]
        
        return None
    
    def _debug_print_tree(self, node, content: str, depth: int = 0, max_depth: int = 3):
        """Debug function to print tree structure"""
        if depth > max_depth:
            return
        
        indent = "  " * depth
        node_text = content[node.start_byte:node.end_byte]
        # Limit text length for readability
        if len(node_text) > 50:
            node_text = node_text[:47] + "..."
        node_text = node_text.replace('\n', '\\n').replace('\r', '\\r')
        
        print(f"{indent}{node.type}: '{node_text}'")
        
        for child in node.children:
            self._debug_print_tree(child, content, depth + 1, max_depth)
