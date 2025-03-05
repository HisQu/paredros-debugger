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
from antlr4.tree.Tree import ParseTreeWalker
from antlr4.atn.PredictionMode import PredictionMode

from paredros_debugger.LookaheadVisualizer import LookaheadVisualizer
from paredros_debugger.DetailedParseListener import DetailedParseListener
from paredros_debugger.UserGrammar import UserGrammar
from paredros_debugger.utils import find_grammar_file, rename_grammar_file, generate_parser, modify_generated_parser, load_parser_and_lexer, get_start_rule

class ParseInformation:
    """Handles the parsing of input using an ANTLR-generated parser and exposes the parse tree."""
    def __init__(self, grammar_folder, input_file_path):
        self.grammar_folder = os.path.abspath(grammar_folder)
        self.input_file = os.path.abspath(input_file_path)
        self.input_text = None
        self.lexer_class = None
        self.parser_class = None
        self.root = None
        self.walker = None
        self.listener = None
        self.grammar_file = None
        self.rules_dict = None
        self.parse_tree = None
        self.tokens = None
        self.lexer = None
        self.parser = None
        self.input_stream = None
        self.traversal = None

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
        
        print("======= Reading input file =======")
        self.input_text = input_text
        print("======= Load parser and lexer =======")
        self.lexer_class, self.parser_class = load_parser_and_lexer(self.grammar_folder)
        print("======= Parsing input text =======")
        self.root = self._parse()
    
    def _parse(self):
        """Runs the parser on the given input text and returns the root parse tree node."""
        print("input stream")
        self.input_stream = InputStream(self.input_text)
        print("lexer")
        self.lexer = self.lexer_class(self.input_stream)
        print("tokens")
        self.tokens = CommonTokenStream(self.lexer)
        print("parser")
        self.parser = self.parser_class(self.tokens)

        self.parser._interp = LookaheadVisualizer(self.parser)
        self.parser._interp.predictionMode = PredictionMode.LL_EXACT_AMBIG_DETECTION
        self.parser.removeErrorListeners()
        self.walker = ParseTreeWalker()
        self.listener = DetailedParseListener(self.parser)

        self.grammar_file = os.path.join(self.grammar_folder, "MyGrammar.g4")
        grammar = UserGrammar()
        grammar.add_grammar_file(self.grammar_file)
        self.rules_dict = grammar.get_rules()
        self.start_rule = get_start_rule(self.grammar_file)
        print("start rule", self.start_rule)
        parse_method = getattr(self.parser, self.start_rule)
        tree = parse_method()
        self.parse_tree = Trees.toStringTree(tree, None, self.parser)
        print("Final Parse Tree")   
        print(self.parse_tree)
        
        self.traversal = self.parser._errHandler.traversal
        merged_groups = self.traversal.group_and_merge()
        self.traversal.replace_merged_nodes(merged_groups)
        self.traversal._fix_node_ids()
        