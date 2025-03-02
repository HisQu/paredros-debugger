# Description: This file contains the ParserInformations class, which is responsible for parsing the input text using an ANTLR-generated parser and lexer.
# The class provides a wrapper around the parse tree nodes to simplify tree traversal and extraction of node information.
# The class also handles the generation and modification of the parser files using the ANTLR tool and the modify_grammar_parser_file.py script.
# The ParserInformations class is used by the CLI tool to parse the input text and generate the parse tree for visualization and debugging.
# The class is designed to be used in conjunction with the CLI tool to provide detailed parsing information and tree traversal capabilities.
# The class encapsulates the parsing logic and provides an easy-to-use interface for accessing the parse tree and node information.
import os
import sys
import subprocess
from antlr4 import InputStream, CommonTokenStream
from antlr4.tree.Trees import Trees
from utils import find_grammar_file, rename_grammar_file, generate_parser, modify_generated_parser, load_parser_and_lexer

class NodeWrapper:
    """Wrapper for ANTLR parse tree nodes to enable easy traversal."""
    def __init__(self, node, parser):
        self.node = node
        self.parser = parser

    def get_text(self):
        return Trees.getNodeText(self.node, self.parser)

    def get_children(self):
        return [NodeWrapper(child, self.parser) for child in self.node.getChildren()]
    
    def __repr__(self):
        return f"NodeWrapper(text={self.get_text()})"

class ParseInformations:
    """Handles the parsing of input using an ANTLR-generated parser and exposes the parse tree."""
    def __init__(self, grammar_folder, input_file_path):
        self.grammar_folder = os.path.abspath(grammar_folder)
        self.input_file = os.path.abspath(input_file_path)

        if not os.path.exists(self.grammar_folder) or not os.path.isdir(self.grammar_folder):
            raise FileNotFoundError(f"The folder {self.grammar_folder} does not exist or is not a directory.")
        
        grammar_file = find_grammar_file(self.grammar_folder)
        if not grammar_file:
            raise FileNotFoundError("No .g4 grammar file found in the provided folder.")
        
        rename_grammar_file(self.grammar_folder, grammar_file)

        try:
            generate_parser(self.grammar_folder)
            print("Parser generated successfully.")
        except subprocess.CalledProcessError:
            print("Error: Failed to generate parser with ANTLR4.")
            sys.exit(1)

        try:
            modify_generated_parser(self.grammar_folder + "/MyGrammarParser.py")
            print("Parser modification completed.")
        except subprocess.CalledProcessError:
            print("Error: Failed to modify the generated parser.")
            sys.exit(1)
        
        try:
            with open(os.path.join(self.input_file), "r", encoding="utf-8") as f:
             input_text = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"The file {self.input_file} does not exist.") from e
        self.input_text = input_text
        
        self.lexer_class, self.parser_class = load_parser_and_lexer(self.grammar_folder)
        self.root = self._parse()
    
    def _parse(self):
        """Runs the parser on the given input text and returns the root parse tree node."""
        input_stream = InputStream(self.input_text)
        lexer = self.lexer_class(input_stream)
        tokens = CommonTokenStream(lexer)
        parser = self.parser_class(tokens)
        start_rule = parser.ruleNames[0]  # Assumes the first rule is the entry point
        parse_method = getattr(parser, start_rule)
        tree = parse_method()
        return NodeWrapper(tree, parser)
    
    def get_root_node(self):
        """Returns the root node of the parsed tree."""
        return self.root