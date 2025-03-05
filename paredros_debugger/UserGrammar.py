from antlr4 import FileStream, CommonTokenStream, InputStream
from antlr4.Token import CommonToken
from typing import Dict, List, Optional, Set
import os
import re

class GrammarRule:
    def __init__(self, name: str, content: str, start_line: int, end_line: int, start_pos: int, end_pos: int):
        self.name = name
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.start_pos = start_pos
        self.end_pos = end_pos

class GrammarFile:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.directory = os.path.dirname(self.path)
        self.rules: Dict[str, GrammarRule] = {}
        self.imports: List[str] = []
        self._load_grammar()
    
    def _load_grammar(self):
        """Load and parse the grammar file"""
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