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
from paredros_debugger.ParseTreeExplorer import ParseTreeExplorer
from paredros_debugger.ParseTraceTree import ParseTraceTree
from paredros_debugger.ParseTraversal import ParseTraversal
from paredros_debugger.utils import generate_parser, modify_generated_parser, load_parser_and_lexer, get_start_rule

class ParseInformation:
    """Handles the parsing of input using an ANTLR-generated parser and exposes the parse tree."""
    def __init__(self, grammar_file_path):
        self.grammar_file = os.path.abspath(grammar_file_path)
        self.grammar_folder = os.path.dirname(self.grammar_file)
        self.input_file = None
        self.input_text = None
        self.lexer_class = None
        self.parser_class = None
        self.root = None
        self.walker = None
        self.listener = None
        self.rules_dict = None
        self.simple_parse_tree = None
        self.parse_trace_tree = None
        self.tokens = None
        self.lexer = None
        self.parser = None
        self.input_stream = None
        self.traversal: ParseTraversal = None
        self.name_without_ext = None

        if not os.path.exists(self.grammar_file) or not os.path.isfile(self.grammar_file):
            raise FileNotFoundError(f"The grammar file {self.grammar_file} does not exist or is not a file.")

        self.grammar = UserGrammar()
        self.grammar.add_grammar_file(self.grammar_file)
        self.rules_dict = self.grammar.get_rules()

        basename = os.path.basename(grammar_file_path)  # Extract grammar file name from path
        print("basename", basename)
        grammar_folder_path = os.path.dirname(grammar_file_path) # Extract grammar folder path
        print("grammar_folder_path", grammar_folder_path)
        self.name_without_ext = os.path.splitext(basename)[0]  # Extracts Grammar name
        print("name_without_ext", self.name_without_ext)

        try:
            generate_parser(grammar_folder_path, basename)
            print("Parser generated successfully.")
        except subprocess.CalledProcessError:
            print("Error: Failed to generate parser with ANTLR4.")
            sys.exit(1)



        try:
            modify_generated_parser(grammar_folder_path + "/" + self.name_without_ext + "Parser.py")
            print("Parser modification completed.")
        except subprocess.CalledProcessError:
            print("Error: Failed to modify the generated parser.")
            sys.exit(1)
    
    def parse(self, input_file):
        """
        Runs the parser on the given input text and set the object with new informations.
        Args:
            None

        Returns:
            None
        
        """
        print("======= Input file location =======")
        print(input_file)
        
        self.input_file = input_file
        # load input string instead of file
        try:
            with open(os.path.join(self.input_file), "r", encoding="utf-8") as f:
                input_text = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"The file {self.input_file} does not exist.") from e
        
        print("======= Reading input file =======")
        self.input_text = input_text
        print("======= Load parser and lexer =======")
        self.lexer_class, self.parser_class = load_parser_and_lexer(self.grammar_folder, self.name_without_ext)
        print("======= Parsing input text =======")
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

        self.start_rule = get_start_rule(self.grammar_file)
        print("start rule", self.start_rule)
        parse_method = getattr(self.parser, self.start_rule)
        tree = parse_method()
        self.simple_parse_tree = Trees.toStringTree(tree, None, self.parser)
        print("Final Parse Tree")
        print(self.simple_parse_tree)

        self.traversal = self.parser._errHandler.traversal
        merged_groups = self.traversal.group_and_merge()
        self.traversal.replace_merged_nodes(merged_groups)
        self.traversal._fix_node_ids()

        self.parse_trace_tree = ParseTraceTree()
        self.parse_trace_tree.build_from_traversal(self.traversal)

        self.explorer = ParseTreeExplorer(full_tree=self.parse_trace_tree, traversal=self.traversal)

    def step_forward(self, step: int) -> None:
        self.explorer.step_forward(num_steps=step)

    def step_backwards(self, step: int) -> None:
        self.explorer.go_back_one_step()

    def go_to_step(self, step: int) -> None:
        self.explorer.reset_to_step_id(step)

    def step_until_next_decision(self) -> None:
        return self.explorer.step_until_next_decision()
    
    def step_back_until_last_decision(self) -> None:
        return self.explorer.step_back_until_previous_decision()
    
    def explore_alternatives(self) -> int:
        self.explorer.expand_alternatives()
        return len(self.explorer._expanded_alt_nodes)

    def choose_alternative(self, alt_index: int) -> None:
        return self.explorer.choose_alternative(alt_index)

    def get_json(self) -> str:
        return self.explorer.to_json()
    
    def get_dict(self) -> dict:
        return self.explorer.to_dict()
    
    def get_current_step(self) -> dict:
        return self.explorer.current_step.to_dict()
    

