"""
This Module contains helper functions for the CLI tool and the ParseInformation class.
The functions are used to generate the parser, modify the generated parser files, and load the parser and lexer classes dynamically.
"""

import importlib
import os
import subprocess
import sys
from paredros_debugger.ModifyGrammarParserFile import modify_parser_file
from antlr4 import CommonTokenStream, Token 
from typing import Optional

def find_grammar_file(folder_path):
    """
    Finds a .g4 grammar file in the given folder path.

    Args:
        folder_path (str): The path to the folder containing the grammar file.

    Returns:
        str: The name of the grammar file if found, otherwise None.
    """
    for file in os.listdir(folder_path):
        if file.endswith(".g4"):
            return file
    return None

def generate_parser(folder_path, grammar_file):
    """
    Runs ANTLR4 to generate the parser in the specified folder.

    Args:
        folder_path (str): The path to the folder containing the grammar file.
        grammar_file (str): The name of the grammar file.

    Returns:
        None
    """
    command = ["antlr4", "-Dlanguage=Python3", grammar_file]
    subprocess.run(command, cwd=folder_path, check=True)

def modify_generated_parser(folder_path):
    """
    Runs the modify_grammar_parser_file.py script to process the generated files and apply CustomParser Naming.

    Args:
        folder_path (str): The path to the folder containing the generated parser files.

    Returns:
        None
    """
    modify_parser_file(folder_path)

def load_parser_and_lexer(folder_path, grammar_name):
    """
    Dynamically load the generated parser and lexer classes from the specified folder.

    Args:
        folder_path (str): The path to the folder containing the generated parser files.
        grammar_name (str): The name of the grammar file.

    Returns:
        tuple: A tuple containing the lexer and parser classes

    """
    sys.path.insert(0, folder_path)  # Ensure the folder is in the Python path

    try:
        lexer = grammar_name + "Lexer"
        parser = grammar_name + "Parser"
        lexer_module = importlib.import_module(lexer)
        parser_module = importlib.import_module(parser)

        lexer_class = getattr(lexer_module, lexer)
        parser_class = getattr(parser_module, parser)

        return lexer_class, parser_class
    except ImportError as e:
        print(f"Error: Unable to load the generated parser/lexer: {e}")
        sys.exit(1)

def get_start_rule(grammar_file):
    """
    Extracts the first rule definition from the grammar file
    to determine the starting rule for parsing.
     
    Args:
        grammar_file (str): The path to the grammar file.

    Returns:
        str: The name of the first rule definition in the grammar
    """
    try:
        with open(grammar_file, 'r', encoding="utf-8") as f:
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


def token_to_dict(token: Token, symbolic_names: list[str]) -> Optional[dict]:
    """
    Converts an ANTLR Token object into a serializable dictionary.

    Args:
        token (Token): The ANTLR Token object.
        symbolic_names (List[str]): The list of symbolic names from the Lexer/Parser.

    Returns:
        Optional[dict]: A dictionary with token info, or None if token is invalid.
    """
    if not isinstance(token, Token):
        return None

    token_type_name = "EOF" # Default for EOF
    if token.type > 0 and token.type < len(symbolic_names):
        token_type_name = symbolic_names[token.type]
    elif token.type == Token.EOF:
         pass
    else:
         token_type_name = "<INVALID>"

    # Use -1 or specific value if index is invalid
    token_index = token.tokenIndex if token.tokenIndex >= 0 else -1

    return {
        "text": token.text,
        "type_name": token_type_name,
        "type_id": token.type,
        "line": token.line,
        "column": token.column,
        "start_index": token.start, # Start char index in input stream
        "stop_index": token.stop,   # Stop char index in input stream
        "token_index": token_index  # Index in the token stream list
    }


def copy_token_stream(original_stream: CommonTokenStream) -> CommonTokenStream:
    """
    Creates a copy of the given CommonTokenStream with the same tokens and index.
    
    :param original_stream: The CommonTokenStream to copy
    :return: A new CommonTokenStream instance with the same tokens and position
    """
    if not isinstance(original_stream, CommonTokenStream):
        raise TypeError("Expected a CommonTokenStream")

    # Create a new stream using the same token source
    copied_stream = CommonTokenStream(original_stream.tokenSource)

    # Copy token list and set the same position
    copied_stream.tokens = original_stream.tokens[:]
    copied_stream.seek(original_stream.index)

    return copied_stream