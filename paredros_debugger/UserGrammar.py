"""
UserGrammar manages the loading and processing of ANTLR grammar files. It handles single
grammar files as well as grammars with imports, tracking rule definitions and their locations.

The module provides three main classes:
- GrammarRule: Represents a single grammar rule with its content and location
- GrammarFile: Handles parsing of individual grammar files
- UserGrammar: Manages multiple grammar files and their relationships
"""

from typing import Dict, List, Optional, Set
import os
import re

class GrammarRule:
    """
    Represents a single rule in an ANTLR grammar with its content and position information.
    """
    def __init__(self, name: str, content: str, start_line: int, end_line: int, start_pos: int, end_pos: int):
        self.name = name
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.start_pos = start_pos
        self.end_pos = end_pos

class GrammarFile:
    """
    Handles parsing and storing information about a single ANTLR grammar file.
    """
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.directory = os.path.dirname(self.path)
        self.rules: Dict[str, GrammarRule] = {}
        self.imports: List[str] = []
        self._load_grammar()
    
    def _load_grammar(self):
        """
        Parses a grammar file to extract rules and imports.
        Processes the file line by line to:
        - Track rule definitions and their contents
        - Record import statements
        - Maintain position information for each rule
        - Handle multi-line rules and rule termination

        Raises:
            FileNotFoundError: If grammar file doesn't exist
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Grammar file not found: {self.path}")
        
        with open(self.path, 'r') as f:
            content = f.read()
            
        # Split content into its lines
        lines = content.split('\n')
        current_rule = ''
        current_content = []
        start_line = 0
        start_pos = 1
        current_pos = 1
        
        for line_num, line in enumerate(lines):
            # Remove indent for parsing but keep original position
            stripped_line = line.strip()

            # Account for the indent
            current_pos = len(line) - len(stripped_line) + 1

            # Check for imports
            if stripped_line.startswith('import'):
                # Extract imported grammar name
                import_match = re.match(r'import\s+([^;]+);?', stripped_line)
                if import_match:
                    imported_grammar = import_match.group(1).strip()
                    self.imports.append(imported_grammar)
                continue

            # Skip comments and grammar definition
            if not stripped_line or stripped_line.startswith('//') or stripped_line.startswith('grammar') or stripped_line.startswith('import'):
                continue
                
            if ':' in stripped_line:
                # If we had a previous rule, save it
                if current_rule:
                    rule_content = ' '.join(current_content)
                    self.rules[current_rule] = GrammarRule(
                        current_rule,
                        rule_content,
                        start_line,
                        line_num -1,
                        start_pos,
                        len(rule_content) + 1
                    )
                
                # Extract rule name and start new rule
                rule_name = line.split(':')[0].strip()
                current_rule = rule_name
                # Keep the full line including the rule name
                current_content = [stripped_line]
                start_line = line_num
                start_pos = current_pos

            elif current_rule:
                # Add lines to current rule content until we find a rule end
                current_content.append(stripped_line)
                # If line ends with semicolon, this rule is complete
                if stripped_line.endswith(';'):
                    rule_content = ' '.join(current_content)
                    self.rules[current_rule] = GrammarRule(
                        current_rule,
                        rule_content,
                        start_line,
                        line_num,
                        start_pos,
                        len(rule_content) + 1
                    )
                    current_rule = ''
                    current_content = []
                    
        # Cleanup when file doesn't end with semicolon or empty line
        if current_rule:
            rule_content = ' '.join(current_content)
            self.rules[current_rule] = GrammarRule(
                current_rule,
                rule_content,
                start_line,
                len(lines) - 1,
                start_pos,
                len(lines[-1]) + 1
            )

class UserGrammar:
    """
    Manages multiple ANTLR grammar files and their relationships.
    Handles the main grammar file and any imported grammar files recursively.

    Attributes:
        grammar_files (Dict[str, GrammarFile]): Loaded grammar files by path
        processed_files (Set[str]): Set of already processed file paths
    """
    def __init__(self):
        self.grammar_files: Dict[str, GrammarFile] = {}
        self.processed_files: Set[str] = set()
        
    def add_grammar_file(self, path: str) -> None:
        """Add a grammar file and recursively process its imports"""
        abs_path = os.path.abspath(path)
        if abs_path in self.processed_files:
            return
            
        self.processed_files.add(abs_path)
        grammar_file = GrammarFile(abs_path)
        self.grammar_files[abs_path] = grammar_file
        
        # Process imports
        base_dir = os.path.dirname(abs_path)
        for imported in grammar_file.imports:
            # Look for the imported grammar file
            import_path = self._find_grammar_file(imported, base_dir)
            if import_path:
                self.add_grammar_file(import_path)
            else:
                raise FileNotFoundError(f"Imported grammar file not found: {imported}")
    
    def _find_grammar_file(self, grammar_name: str, search_dir: str) -> Optional[str]:
        """Find a grammar file by name in the given directory"""
        # Try exact name
        exact_path = os.path.join(search_dir, grammar_name)
        if os.path.exists(exact_path):
            return exact_path
            
        # Try with .g4 extension
        g4_path = os.path.join(search_dir, f"{grammar_name}.g4")
        if os.path.exists(g4_path):
            return g4_path
            
        return None
    
    def get_rules(self) -> Dict[str, GrammarRule]:
        """Get all rules from all grammar files"""
        all_rules = {}
        for grammar_file in self.grammar_files.values():
            all_rules.update(grammar_file.rules)
        return all_rules
    
    def get_rule_by_name(self, name: str) -> Optional[GrammarRule]:
        """Get a specific rule by name"""
        for grammar_file in self.grammar_files.values():
            if name in grammar_file.rules:
                return grammar_file.rules[name]
        return None