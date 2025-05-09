# Description: This file contains the ParserInformations class, which is responsible for parsing the input text using an ANTLR-generated parser and lexer.
# The class provides a wrapper around the parse tree nodes to simplify tree traversal and extraction of node information.
# The class also handles the generation and modification of the parser files using the ANTLR tool and the modify_grammar_parser_file.py script.
# The ParserInformations class is used by the CLI tool to parse the input text and generate the parse tree for visualization and debugging.
# The class is designed to be used in conjunction with the CLI tool to provide detailed parsing information and tree traversal capabilities.
# The class encapsulates the parsing logic and provides an easy-to-use interface for accessing the parse tree and node information.
import os
import sys
import subprocess
from typing import Optional, Any
import warnings

from antlr4 import InputStream, CommonTokenStream, Token
from antlr4.tree.Trees import Trees
from antlr4.tree.Tree import ParseTreeWalker
from antlr4.atn.PredictionMode import PredictionMode

from paredros_debugger.LookaheadVisualizer import LookaheadVisualizer
from paredros_debugger.DetailedParseListener import DetailedParseListener
from paredros_debugger.UserGrammar import UserGrammar, GrammarRule 
from paredros_debugger.ParseTreeExplorer import ParseTreeExplorer
from paredros_debugger.ParseTraceTree import ParseTraceTree, ParseTreeNode
from paredros_debugger.ParseTraversal import ParseTraversal
from paredros_debugger.ParseStep import ParseStep
from paredros_debugger.utils import (
    generate_parser, modify_generated_parser, load_parser_and_lexer,
    get_start_rule, token_to_dict
)
class ParseInformation:
    """
    Manages the ANTLR parsing process, stores results, and provides an API
    for exploring the parse steps and tree, designed for use by a debugging frontend.

    Responsibilities:
    - Locating and processing the grammar (.g4) file.
    - Loading the generated parser/lexer.
    - Parsing input text and capturing detailed step-by-step traversal info.
    - Building a structured parse tree (`ParseTraceTree`) from the traversal.
    - Providing methods to navigate the parse steps (forward, back, jump).
    - Offering methods to query current state (step info, tree node info, context).
    - Exposing grammar details (rule locations) and the token list.
    """
    def __init__(self, grammar_file_path: str):
        """
        Initializes the ParseInformation instance.

        Loads the grammar, generates/modifies ANTLR code if necessary.

        Args:
            grammar_file_path (str): Path to the main .g4 grammar file.
        """
        if not os.path.exists(grammar_file_path) or not os.path.isfile(grammar_file_path):
             raise FileNotFoundError(f"The grammar file '{grammar_file_path}' does not exist or is not a file.")

        self.grammar_file: str = os.path.abspath(grammar_file_path)
        self.grammar_folder: str = os.path.dirname(self.grammar_file)
        self.input_file: Optional[str] = None
        self.input_text: Optional[str] = None
        self.lexer_class: Optional[type] = None
        self.parser_class: Optional[type] = None
        self.lexer: Optional[Any] = None # Store instance
        self.parser: Optional[Any] = None # Store instance
        self.tokens: Optional[CommonTokenStream] = None
        self.token_data_list: list[dict] = [] # <<< NEW: Explicit token list

        self.grammar: UserGrammar = UserGrammar()
        self.grammar.add_grammar_file(self.grammar_file)
        # self.rules_dict: Dict[str, GrammarRule] = self.grammar.get_rules() # Can get on demand

        self.traversal: Optional[ParseTraversal] = None
        self.parse_trace_tree: Optional[ParseTraceTree] = None
        self.explorer: Optional[ParseTreeExplorer] = None

        self.name_without_ext: str = os.path.splitext(os.path.basename(grammar_file_path))[0]

    def generate_parser(self): 
        """
        Responsibilities:
            - Generating and modifying ANTLR parser/lexer code.
        Raises:
            FileNotFoundError: If the grammar file does not exist.
            subprocess.CalledProcessError: If ANTLR generation or modification fails.
        """
        # --- Generation & Modification ---
        # (Keep existing generation/modification logic)
        try:
             print(f"Attempting to generate parser for: {self.name_without_ext} in {self.grammar_folder}")
             generate_parser(self.grammar_folder, self.grammar_file)
             print("Parser generation successful (or already up-to-date).")
        except subprocess.CalledProcessError as e:
             ln1=f"Error: Failed to generate parser with ANTLR4. Command: {e.cmd}, Return code: {e.returncode}"
             ln2=f"Output:\n{e.output}\nStderr:\n{e.stderr}"
             print(ln1)
             print(ln2)
             raise Exception(ln1+"\n"+ln2)
        except FileNotFoundError:
             ln="Error: 'antlr4' command not found. Is ANTLR4 installed and in your PATH?"
             print(ln)
             raise Exception(ln)

        parser_file_to_modify = os.path.join(self.grammar_folder, self.name_without_ext + "Parser.py")
        if os.path.exists(parser_file_to_modify):
            try:
                modify_generated_parser(parser_file_to_modify)
                print("Parser modification completed.")
            except Exception as e: # Broader catch for file IO etc.
                print(f"Warning: Failed to modify the generated parser '{parser_file_to_modify}'. Error: {e}")
                # Decide if this is critical - maybe proceed if parser loads anyway?
        else:
             print(f"Warning: Expected parser file '{parser_file_to_modify}' not found after generation.")
             # This is likely an error state

        # --- Load Classes ---
        try:
             self.lexer_class, self.parser_class = load_parser_and_lexer(self.grammar_folder, self.name_without_ext)
             print("Lexer and Parser classes loaded.")
        except ImportError as e:
             ln1=f"Error loading generated Python modules: {e}"
             ln2="Ensure the grammar folder is accessible and Python files were generated correctly."
             raise Exception(ln1+"\n"+ln2)
        except AttributeError as e:
            ln=f"Error finding Lexer/Parser class in generated modules: {e}"
            print(ln)
            raise Exception(ln)

    def parse(self, input_file_path: str):
        """
        Parses the content of the given input file.

        - Reads the input file.
        - Performs lexing and parsing using the loaded ANTLR classes.
        - Captures the detailed parse traversal.
        - Builds the final `ParseTraceTree`.
        - Initializes the `ParseTreeExplorer`.

        Args:
            input_file_path (str): Path to the input file to parse.

        Raises:
            FileNotFoundError: If the input file cannot be found or read.
            Exception: If parsing fails critically.
        """
        self.input_file = os.path.abspath(input_file_path)
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"The input file '{self.input_file}' does not exist.")

        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                self.input_text = f.read()
        except IOError as e:
            raise IOError(f"Could not read input file '{self.input_file}': {e}") from e

        if self.input_text is None:
             raise ValueError("Input text could not be read.")
        if not self.lexer_class or not self.parser_class:
             raise RuntimeError("Lexer or Parser class not loaded. Initialize first using `generate_parser`.")

        print("======= Parsing Input =======")
        self.input_stream = InputStream(self.input_text)
        self.lexer = self.lexer_class(self.input_stream)
        self.tokens = CommonTokenStream(self.lexer)

        # Create Explicit Token List
        self.token_data_list = []
        self.lexer.reset()
        all_raw_tokens = self.lexer.getAllTokens()
        symbolic_names = getattr(self.lexer, 'symbolicNames', []) # Get symbolic names safely

        for token in all_raw_tokens:
             token_dict = token_to_dict(token, symbolic_names)
             if token_dict:
                 self.token_data_list.append(token_dict)
        print(f"Created token list with {len(self.token_data_list)} tokens.")

        # Reset token stream position after iterating through lexer
        self.input_stream = InputStream(self.input_text)
        self.lexer = self.lexer_class(self.input_stream)
        self.tokens = CommonTokenStream(self.lexer) 

        self.parser = self.parser_class(self.tokens)

        # Setup custom interpreter and error strategy
        self.parser._interp = LookaheadVisualizer(self.parser)
        # Ensure the custom error handler (via CustomParser) has the parser reference
        if hasattr(self.parser, '_errHandler') and hasattr(self.parser._errHandler, 'traversal'):
             self.traversal = self.parser._errHandler.traversal
             self.traversal.set_parser(self.parser) # Ensure traversal knows the parser
        else:
             print("Warning: CustomParser or CustomDefaultErrorStrategy not correctly integrated.")
             raise RuntimeError("ParseTraversal could not be obtained from parser's error handler.")


        # Configure prediction mode if needed (LL_EXACT_AMBIG_DETECTION is expensive)
        # self.parser._interp.predictionMode = PredictionMode.LL # Faster, less ambiguity info
        self.parser._interp.predictionMode = PredictionMode.LL_EXACT_AMBIG_DETECTION

        # Remove default error listeners if custom handling is sufficient
        self.parser.removeErrorListeners()
        self.walker = ParseTreeWalker()
        self.listener = DetailedParseListener(self.parser)

        # Determine start rule and parse
        start_rule_name = get_start_rule(self.grammar_file)
        if not start_rule_name:
            raise RuntimeError("Could not determine the start rule from the grammar file.")
        if not hasattr(self.parser, start_rule_name):
            raise RuntimeError(f"Parser class does not have the start rule method '{start_rule_name}'.")

        print(f"Starting parse with rule: {start_rule_name}")
        parse_method = getattr(self.parser, start_rule_name)
        _ = parse_method() # <<<<< THIS IS WHERE THE PARSING HAPPENS

        print("======= Parsing Complete =======")

        # Post-process traversal (merging, fixing IDs)
        if self.traversal:
            merged_groups = self.traversal.group_and_merge()
            self.traversal.replace_merged_nodes(merged_groups)
            self.traversal._fix_node_ids() # Renumber IDs sequentially
        else:
            print("Warning: No traversal data captured.")

        # Build the ParseTraceTree from the processed traversal
        self.parse_trace_tree = ParseTraceTree()
        if self.traversal:
            self.parse_trace_tree.build_from_traversal(self.traversal)
        else:
             # Create an empty tree or handle error
             pass

        # Initialize the explorer
        if self.parse_trace_tree and self.traversal:
            self.explorer = ParseTreeExplorer(full_tree=self.parse_trace_tree, traversal=self.traversal)
        else:
             raise RuntimeError("Failed to initialize ParseTreeExplorer due to missing tree or traversal.")

        print("ParseInformation setup complete.")


    # --- API Methods for Frontend ---

    def get_input_text(self) -> Optional[str]:
        """Returns the full input text that was parsed."""
        return self.input_text

    def get_token_list(self) -> list[dict]:
        """
        Returns a list of all tokens generated by the lexer.
        Each token is represented as a dictionary with keys like:
        'text', 'type_name', 'type_id', 'line', 'column',
        'start_index', 'stop_index', 'token_index'.
        """
        return self.token_data_list

    def get_grammar_rule_info(self, rule_name: str) -> Optional[dict]:
        """
        Provides information about a specific grammar rule definition.

        Args:
            rule_name (str): The name of the grammar rule.

        Returns:
            Optional[Dict]: A dictionary containing 'name', 'content', 'file_path',
                           'start_line', 'end_line', 'start_pos', 'end_pos'
                           if the rule is found, otherwise None.
        """
        rule: Optional[GrammarRule] = self.grammar.get_rule_by_name(rule_name)
        if not rule:
            return None

        # Find which file this rule belongs to (needed for file_path)
        rule_file_path = None
        for path, grammar_file_obj in self.grammar.grammar_files.items():
            if rule_name in grammar_file_obj.rules:
                rule_file_path = path
                break

        return {
            "name": rule.name,
            "content": rule.content,
            "file_path": rule_file_path,
            "start_line": rule.start_line,
            "end_line": rule.end_line,
            "start_pos": rule.start_pos,
            "end_pos": rule.end_pos
        }

    def get_current_parse_step_info(self) -> Optional[dict]:
        """
        Returns detailed information about the currently active parse step (`ParseStep`).

        Includes basic step data, token index, rule stack, and grammar rule location.

        Returns:
            Optional[Dict]: A dictionary with comprehensive step details, or None if
                           no explorer or current step is available.
        """
        if not self.explorer:
            return None

        current_step: Optional[ParseStep] = self.explorer.current_step
        if not current_step:
            return None

        # Get base step data
        step_data = current_step.to_dict(include_transitions=True) # Include transitions here

        # Add grammar rule location if rule_name exists
        if current_step.rule_name:
            step_data["grammar_rule_location"] = self.get_grammar_rule_info(current_step.rule_name)
        else:
            step_data["grammar_rule_location"] = None

        # Add input text snippet (Context Window)
        step_data["input_context_snippet"] = self._get_input_context_snippet(current_step.token_index)

        return step_data

    def _get_input_context_snippet(self, token_index: Optional[int], window_size: int = 40) -> Optional[str]:
        """
        Generates a snippet of the input text centered around the token at token_index.

        Args:
            token_index (Optional[int]): The index of the token in `self.token_data_list`.
            window_size (int): The approximate number of characters desired around the token.

        Returns:
            Optional[str]: The text snippet with the token highlighted, or None.
        """
        if token_index is None or not self.input_text or not self.token_data_list or token_index >= len(self.token_data_list):
             return None

        token_info = self.token_data_list[token_index]
        start_char = token_info['start_index']
        stop_char = token_info['stop_index']

        # Calculate window boundaries
        half_window = window_size // 2
        snippet_start = max(0, start_char - half_window)
        snippet_end = min(len(self.input_text), stop_char + 1 + half_window) # +1 because stop is inclusive

        # Adjust if window goes out of bounds
        if snippet_start == 0:
            snippet_end = min(len(self.input_text), window_size)
        if snippet_end == len(self.input_text):
            snippet_start = max(0, len(self.input_text) - window_size)

        # Extract snippet and add markers
        prefix = self.input_text[snippet_start:start_char]
        token_text = self.input_text[start_char : stop_char + 1]
        suffix = self.input_text[stop_char + 1 : snippet_end]

        # Indicate truncation
        prefix_marker = "..." if snippet_start > 0 else ""
        suffix_marker = "..." if snippet_end < len(self.input_text) else ""

        return f"{prefix_marker}{prefix}[{token_text}]{suffix}{suffix_marker}"


    def get_current_parse_tree_node_info(self) -> Optional[dict]:
        """
        Returns information about the ParseTreeNode that contains the current step_id.

        Returns:
            Optional[Dict]: Dictionary with 'id', 'node_type', 'rule_name', 'token',
                           or None if not found.
        """
        if not self.explorer or not self.explorer.working_tree or not self.explorer.working_tree.root:
            return None

        # Use the explorer's helper or reimplement search here
        pt_node: Optional[ParseTreeNode] = self.explorer._find_ptnode_in_working(self.explorer.current_step_id)

        if not pt_node:
             return None

        return {
            "id": pt_node.id,
            "node_type": "token" if pt_node.token else "rule",
            "rule_name": pt_node.rule_name,
            "token": pt_node.token,
        }

    def get_highlighting_info_for_node(self, node_id: str) -> Optional[dict[str, Any]]:
        """
        Calculates the token and character range corresponding to a specific
        ParseTreeNode ID in the current working tree.

        This is useful for highlighting the input text that a rule node represents.

        Args:
            node_id (str): The unique ID of the ParseTreeNode (e.g., "ptn_5")
                           for which to get highlighting information.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing:
                - 'start_token_index': Index of the first token in the range.
                - 'end_token_index': Index of the last token in the range.
                - 'start_char_index': Character start position in the input text.
                - 'end_char_index': Character end position (inclusive) in the input text.
            Returns None if the node is not found, is not a rule node, lacks
            entry/exit steps, or if indices are invalid.
        """
        if not self.explorer or not self.explorer.working_tree or not self.explorer.working_tree.root:
            warnings.warn("Explorer or working tree not available for highlighting.")
            return None
        if not self.token_data_list:
             warnings.warn("Token list not available for highlighting.")
             return None

        # 1. Find the ParseTreeNode by its ID in the working tree
        #    We need access to the node's trace_steps. This might require
        #    a helper in ParseTreeExplorer or searching the tree dict structure.
        #    Let's assume we can find the node object or its data.
        #    (Using explorer's internal method for now, might need refinement)
        pt_node: Optional[ParseTreeNode] = None
        queue = [self.explorer.working_tree.root]
        while queue:
            cur = queue.pop(0)
            if cur.id == node_id:
                pt_node = cur
                break
            queue.extend(cur.children)

        if not pt_node:
            # warnings.warn(f"ParseTreeNode with ID '{node_id}' not found in working tree.")
            return None # Node not found

        # Ensure it's a rule node, as token nodes represent single tokens
        if pt_node.token is not None:
            # For token nodes, highlighting info comes directly from its single token
            # Find the corresponding token step
            token_step = next((step for step in pt_node.trace_steps if step.node_type == "Token consume"), None)
            if token_step and token_step.token_index is not None and token_step.token_index < len(self.token_data_list):
                 token_info = self.token_data_list[token_step.token_index]
                 return {
                     'start_token_index': token_step.token_index,
                     'end_token_index': token_step.token_index,
                     'start_char_index': token_info['start_index'],
                     'end_char_index': token_info['stop_index'],
                 }
            else:
                 warnings.warn(f"Could not find valid token info for token node ID '{node_id}'.")
                 return None


        # 2. Find Rule Entry and Exit steps within the node's trace_steps
        entry_step: Optional[ParseStep] = None
        exit_step: Optional[ParseStep] = None
        # This assumes trace_steps are available. If using non-verbose tree dict,
        # this info might be missing and require fetching verbose data.
        if not hasattr(pt_node, 'trace_steps') or not pt_node.trace_steps:
             warnings.warn(f"Node ID '{node_id}' lacks trace_steps, cannot determine range. Fetch tree with verbose=True?")
             return None

        for step in pt_node.trace_steps:
            if step.node_type == "Rule entry":
                entry_step = step
            elif step.node_type == "Rule exit":
                exit_step = step
            # Optimization: break if both found? Depends if multiple entries/exits are possible per node.

        if not entry_step:
            # Handle case where entry step might be missing (e.g., start rule?)
            # For now, return None if entry is missing for a rule node.
            # Or potentially default start_token_idx to 0 if it's the root? Needs careful thought.
             warnings.warn(f"Rule entry step not found for node ID '{node_id}'.")
             return None
        if not exit_step:
             warnings.warn(f"Rule exit step not found for node ID '{node_id}'.")
             return None # Cannot determine end without exit step

        # 3. Extract token indices
        start_token_idx = entry_step.token_index
        exit_token_idx = exit_step.token_index # Index *after* the last consumed token

        if start_token_idx is None:
            warnings.warn(f"Rule entry step for node ID '{node_id}' has no token index.")
            return None
        if exit_token_idx is None:
             warnings.warn(f"Rule exit step for node ID '{node_id}' has no token index.")
             return None

        # 4. Calculate end token index
        end_token_idx = exit_token_idx - 1

        # 5. Validate indices
        if end_token_idx < start_token_idx:
            # This can happen for empty rules or potentially errors
            # warnings.warn(f"Calculated end token index ({end_token_idx}) is before start ({start_token_idx}) for node ID '{node_id}'.")
            # Return range covering just the start token? Or None? Let's return None for now.
            return None
        if start_token_idx >= len(self.token_data_list) or end_token_idx >= len(self.token_data_list):
             warnings.warn(f"Token indices ({start_token_idx}, {end_token_idx}) out of bounds for token list (len={len(self.token_data_list)}) for node ID '{node_id}'.")
             return None

        # 6. Get character range from token list
        try:
            start_char_idx = self.token_data_list[start_token_idx]['start_index']
            end_char_idx = self.token_data_list[end_token_idx]['stop_index']
        except IndexError:
             warnings.warn(f"IndexError accessing token_data_list for indices ({start_token_idx}, {end_token_idx}) for node ID '{node_id}'.")
             return None
        except KeyError:
             warnings.warn(f"KeyError accessing 'start_index' or 'stop_index' in token_data_list for node ID '{node_id}'.")
             return None


        # 7. Return results
        return {
            'start_token_index': start_token_idx,
            'end_token_index': end_token_idx,
            'start_char_index': start_char_idx,
            'end_char_index': end_char_idx,
            'node_id': node_id # Include original node ID for reference
        }

    # --- Navigation Methods (with improved docstrings) ---

    def step_forward(self, steps: int = 1) -> None:
        """
        Moves the current parse step forward by the specified number of steps.
        Updates the internal state and the explorable `working_tree`.

        Args:
            steps (int): Number of steps to move forward (default: 1).

        Raises:
            RuntimeError: If stepping beyond the end of the parse or other issues occur.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.step_forward(num_steps=steps)

    def step_backwards(self, steps: int = 1) -> None:
        """
        Moves the current parse step backward by the specified number of steps.
        Currently only supports stepping back one step at a time.
        Updates the internal state and the explorable `working_tree`.

        Args:
            steps (int): Number of steps to move backward (must be 1).

        Raises:
            RuntimeError: If already at the beginning or other issues occur.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        if steps != 1: raise ValueError("Currently only stepping back 1 step is supported.")
        self.explorer.go_back_one_step() # Renamed internally for consistency

    def go_to_step(self, step_id: int) -> None:
        """
        Resets the explorer to a specific step ID.
        Updates the internal state and the explorable `working_tree`.

        Args:
            step_id (int): The target step ID to jump to.

        Raises:
            RuntimeError: If the step ID is invalid or out of bounds.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.reset_to_step_id(step_id)

    def step_until_next_decision(self) -> None:
        """
        Advances the current step forward until a decision point (a step with
        multiple possible transitions) is reached, or the end of the parse.

        Raises:
            RuntimeError: If stepping fails.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.step_until_next_decision()

    def step_back_until_previous_decision(self) -> None: # Renamed for consistency
        """
        Moves the current step backward until a decision point (a step with
        multiple possible transitions) is reached, or the beginning of the parse.

        Raises:
            RuntimeError: If stepping back fails.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.step_back_until_previous_decision()

    def expand_alternatives(self) -> int:
        """
        If the current step is a decision point, this method prepares the
        alternative parse paths for exploration. It modifies the `working_tree`
        to show these alternatives temporarily.

        Call `choose_alternative` or `cancel_alt_expansion` afterwards.

        Returns:
            int: The number of available alternative paths (including the original one if applicable).

        Raises:
            RuntimeError: If the current step is not a decision point or expansion fails.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        # The explorer's expand_alternatives now returns void, but we can get count
        self.explorer.expand_alternatives()
        return len(self.explorer._expanded_alt_nodes)


    def choose_alternative(self, alt_index: int) -> None:
        """
        Selects one of the alternatives previously expanded by `expand_alternatives`.
        The `working_tree` is updated to follow this chosen path, and other
        alternatives are pruned. The current step may advance.

        Args:
            alt_index (int): The 1-based index of the alternative to choose.

        Raises:
            RuntimeError: If not in alternative expansion mode or the index is invalid.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.choose_alternative(alt_index)

    def cancel_alt_expansion(self) -> None:
        """
        Cancels the alternative expansion mode initiated by `expand_alternatives`.
        Removes the temporary alternative branches from the `working_tree`.
        """
        if not self.explorer: raise RuntimeError("Explorer not initialized.")
        self.explorer.cancel_alt_expansion()

    # --- Output Methods ---

    def get_current_tree_json(self, verbose: bool = False) -> str:
        """
        Returns the current state of the explorable parse tree (`working_tree`)
        as a JSON string.

        Args:
            verbose (bool): If True, includes detailed trace step info within each node.

        Returns:
            str: JSON representation of the working tree. Returns "{}" if no tree exists.
        """
        if not self.explorer: return "{}"
        return self.explorer.to_json(verbose=verbose)

    def get_current_tree_dict(self, verbose: bool = False) -> dict:
        """
        Returns the current state of the explorable parse tree (`working_tree`)
        as a Python dictionary.

        Args:
            verbose (bool): If True, includes detailed trace step info within each node.

        Returns:
            dict: Dictionary representation of the working tree. Returns {} if no tree exists.
        """
        if not self.explorer: return {}
        return self.explorer.to_dict(verbose=verbose)

    # --- Deprecated/Internal Access (Avoid if possible) ---
    def step_back_until_last_decision(self) -> None:
        """
        DEPRECATED: Use step_back_until_previous_decision() instead.
        Moves the current step backward until a decision point is reached.
        """
        warnings.warn(
            "The 'step_back_until_last_decision()' method is deprecated. Use 'step_back_until_previous_decision()' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Call the new method (assuming it exists as named)
        self.step_back_until_previous_decision()

    def explore_alternatives(self) -> int:
        """
        DEPRECATED: Use expand_alternatives() instead.
        Prepares alternative parse paths for exploration.
        """
        warnings.warn(
            "The 'explore_alternatives()' method is deprecated. Use 'expand_alternatives()' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Call the new method (assuming it exists as named)
        return self.expand_alternatives()

    def get_json(self) -> str:
        """
        DEPRECATED: Use get_current_tree_json(verbose=False) instead.
        Returns the current state of the explorable parse tree as a JSON string.
        """
        warnings.warn(
            "The 'get_json()' method is deprecated. Use 'get_current_tree_json(verbose=False)' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Call the new method (assuming it exists as named)
        return self.get_current_tree_json(verbose=False)

    def get_dict(self) -> dict:
        """
        DEPRECATED: Use get_current_tree_dict(verbose=False) instead.
        Returns the current state of the explorable parse tree as a Python dictionary.
        """
        warnings.warn(
            "The 'get_dict()' method is deprecated. Use 'get_current_tree_dict(verbose=False)' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Call the new method (assuming it exists as named)
        return self.get_current_tree_dict(verbose=False)

    def get_current_step(self) -> dict:
        """
        DEPRECATED: Use get_current_parse_step_info() instead.
        Returns basic information about the currently active parse step.
        """
        warnings.warn(
            "The 'get_current_step()' method is deprecated. Use 'get_current_parse_step_info()' which provides richer details.",
            DeprecationWarning,
            stacklevel=2
        )
        # Call the new method (assuming it exists as named)
        step_info = self.get_current_parse_step_info()
        return step_info if step_info else {}