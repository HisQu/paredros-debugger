import importlib
from paredros_debugger.modify_grammar_parser_file import modify_parser_file
import os
import subprocess
import sys

def find_grammar_file(folder_path):
    """Finds a .g4 grammar file in the given folder path."""
    for file in os.listdir(folder_path):
        if file.endswith(".g4"):
            return file
    return None

def rename_grammar_file(folder_path, grammar_file):
    """Renames the found grammar file to MyGrammar.g4."""
    old_path = os.path.join(folder_path, grammar_file)
    new_path = os.path.join(folder_path, "MyGrammar.g4")
    os.rename(old_path, new_path)
    return new_path

def generate_parser(folder_path):
    """Runs ANTLR4 to generate the parser in the specified folder."""
    command = ["antlr4", "-Dlanguage=Python3", "MyGrammar.g4"]
    subprocess.run(command, cwd=folder_path, check=True)

def modify_generated_parser(folder_path):
    """Runs the modify_grammar_parser_file.py script to process the generated files."""
    modify_parser_file(folder_path)

def load_parser_and_lexer(folder_path):
    """Dynamically load the generated MyGrammarLexer and MyGrammarParser."""
    sys.path.insert(0, folder_path)  # Ensure the folder is in the Python path

    try:
        lexer_module = importlib.import_module("MyGrammarLexer")
        parser_module = importlib.import_module("MyGrammarParser")

        lexer_class = getattr(lexer_module, "MyGrammarLexer")
        parser_class = getattr(parser_module, "MyGrammarParser")

        return lexer_class, parser_class
    except ImportError as e:
        print(f"Error: Unable to load the generated parser/lexer: {e}")
        sys.exit(1)

def get_start_rule(grammar_file):
    """Extracts the first rule definition from the grammar file
    to determine the starting rule for parsing."""
    try:
        with open(grammar_file, 'r') as f:
            for line in f:
                # Skip empty lines and comments
                if line.strip() and not line.strip().startswith('//'):
                    # Look for the first rule definition
                    if ':' in line:
                        # Extract rule name before the colon
                        extracted_rule_names = line.split(':')[0].strip()
                        return extracted_rule_names
    except FileNotFoundError:
        return ''
