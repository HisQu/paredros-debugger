"""
ParseStep represents a node in the parser's traversal graph. Each node captures a specific point 
in the parsing process, including the current state, available transitions, and parsing decisions.

The node can represent different types of parsing events:
- Decision points (where the parser must choose between alternatives)
- Rule entries/exits 
- Token consumption
- Error states

Each node maintains:
- Its current ATN state and parser context
- Available parsing alternatives
- Chosen alternative
- Links to parent/next nodes
- Alternative paths that could have been taken

The node structure forms a directed graph where:
- next_node points to the sequential parsing path
- next_node_alternatives contain branching possibilities
- parent points to the previous parsing step

Example node types:
- Decision: Parser choosing between multiple valid paths
- Rule entry: Entering a grammar rule
- Rule exit: Completing a grammar rule
- Token consume: Matching an input token
- Error: Parsing failure point
"""

from pprint import pprint
import json

from antlr4.atn.Transition import *
from antlr4.BufferedTokenStream import TokenStream
from antlr4.Parser import Parser

class ParseStep:
    def __init__(self, state, current_token, lookahead, possible_alternatives, input_text, rule, node_type, token_stream:TokenStream, parent_id=-1):
        """
        Initialize a new parse node.

        Args:
            state: ATN state number or object
            current_token: Current token being processed
            lookahead: List of upcoming tokens
            possible_alternatives: Available parsing alternatives to traverse into as (state, tokens) pairs
            input_text: Current input context with cursor position
            rule: Current grammar rule name
            node_type: Type of node (Decision, Rule entry/exit, Token consume, Error)
            parent_id: ID of parent node for sequential numbering (-1 for root)
        """
        self.state = state                                  # ATN state number
        self.current_token = current_token                  # Current token being processed 
        self.lookahead = lookahead                          # List of upcoming tokens
        self.chosen_index = -1                              # Chosen alternative (if known)
        self.input_text = input_text                        # Current input context
        self.next_node = None                               # Next node in the traversal sequence           
        self.next_node_verbose = None                       # Verbose representation of the next node
        self.parent = None                                  # Parent node
        self.possible_alternatives : list[tuple[int, list[str]]] = possible_alternatives  # Available parsing alternatives
        self.next_node_alternatives : list[ParseStep] = []  # The nodes that follow the next transition from this node
        self.next_node_alternatives_verbose = []            # Verbose representation of the alternative nodes
        self.id = (parent_id + 1) if isinstance(parent_id, int) and parent_id >= 0 else 0  # Unique ID within its branch
        self.rule_name = rule                               # Current rule name
        self.has_error = False                              # Flag for error nodes
        self.node_type = node_type                          # Type of node (Decision, Rule, Token, Error)
        self.matching_error = False                         # Flag for token matching errors
        self.token_stream = token_stream                    # Token stream for the current node
        self.next_input_token = None                        # current input Lexer token being processed
        self.next_input_literal = None                      # current input literal token being processed

    def add_next_node(self, next_node):
        """
        Add a sequential transition to the next node in the parse traversal.
        This represents the actual path taken during parsing.

        Args:
            next_node (ParseStep): The node to add as the next sequential step

        Note:
            - Sets bidirectional link between nodes (next_node and parent)
            - Updates the next node's ID to maintain sequential numbering
        """
        self.next_node = next_node
        next_node.parent = self
        next_node.id = self.id + 1

    def get_verbose_node(self):
        """
        Get the verbose representation of the next node
        
        Args:
            None
        
        Returns:
            str: Verbose representation of the next node
        """
        if self.next_node is None:
            return None
        return f"state: {self.next_node.state}, rule_name: {self.next_node.rule_name}, node_type: {self.next_node.node_type}"

    def get_next_node_alternatives_verbose(self):
        """Get the verbose representation of the possible alternatives"""
        for alternative in self.next_node_alternatives:
            self.next_node_alternatives_verbose.append(f"name: {alternative.rule_name}, state: {alternative.state}, tokens: {alternative.current_token}")
        return self.next_node_alternatives_verbose

    def add_alternative_node(self, alt_node):
        """
        Add a branching alternative node representing a possible parse path.
        These nodes represent paths the parser could have taken but didn't.

        Args:
            alt_node (ParseStep): The node representing an alternative parse path

        Note:
            - Alternative nodes get IDs like "Alt 1", "Alt 2" etc.
            - Sets parent link back to this node
        """
        self.next_node_alternatives.append(alt_node)
        alt_node.parent = self
        alt_node.id = str(self.id) + "." + str(len(self.next_node_alternatives))

    def get_unique_identifier(self):
        """Get unique identifier combining ID and state"""
        return f"{self.id}"

    def set_error(self):
        """Mark this node as having an error"""
        self.has_error = True

    def print_attributes(self):
        """Pretty Print the object's attributes."""
        self.next_node_verbose = self.get_verbose_node()
        self.next_node_alternatives_verbose = self.get_next_node_alternatives_verbose()
        pprint(vars(self))

    def get_attributes_next_node(self):
        """Returns the object's attributes as a dictionary."""
        return json.dumps(vars(self.next_node), indent=4, ensure_ascii=False)

    def get_attributes_as_json(self):
        """Returns the object's attributes as a JSON string."""
        return json.dumps(vars(self), indent=4, ensure_ascii=False)

    def matches_rule_entry(self, ruleName: str) -> bool:
        """
        Check if this node's alternatives include entering the specified rule.
        Used by error handler to track rule entry decisions.

        Args:
            ruleName (str): Name of the rule to check for

        Returns:
            bool: True if one of the alternatives enters this rule
        """
        for alt_state, tokens in self.possible_alternatives:
            if any(t.startswith('Rule') and ruleName in t for t in tokens):
                return True
        return False
    
    def matches_token(self, token_str: str) -> bool:
        """
        Check if this node's alternatives include matching the given token.
        Used by error handler to track token consumption decisions.
        Handles both literal tokens ('a', '(') and typed tokens (INT, ID).

        Args:
            token_str (str): Token to match against

        Returns:
            bool: True if one of the alternatives matches this token
        """
        # Handle literals
        if token_str.startswith("Literal"):
            literal_value = token_str.split("'")[1]  # Extract '(' from "Literal ('(')"
            for target_state, tokens in self.possible_alternatives:
                if any(t.startswith("'") and t.strip("'") == literal_value for t in tokens):
                    return True
        # Handle token types
        else:
            token_parts = token_str.split(" ")  # Split "INT ('4')" into ["INT", "('4')"]
            token_type = token_parts[0]         # Get "INT"
            token_instance = token_str.split("'")[1]  # Get "4" from "('4')"

            for target_state, tokens in self.possible_alternatives:
                # Check if either the token type or the actual value matches
                if any(t == token_type or token_instance == t.strip("'") for t in tokens):
                    return True
        return False

    def get_matching_alternative(self, token_str: str) -> int:
        """
        Find which alternative matches the given token and return its index.
        Used by error handler to determine which path was taken when consuming a token.

        Args:
            token_str (str): Token to match against

        Returns:
            int: 1-based index of matching alternative, or -1 if no match found
        """
        # Handle literals
        if token_str.startswith("Literal"):
            literal_value = token_str.split("'")[1]
            for i, (target_state, tokens) in enumerate(self.possible_alternatives):
                if any(t.startswith("'") and t.strip("'") == literal_value for t in tokens):
                    return i + 1
        # Handle token types
        else:
            token_parts = token_str.split(" ") 
            token_type = token_parts[0]  
            token_instance = token_str.split("'")[1]
            for i, (target_state, tokens) in enumerate(self.possible_alternatives):
                if any(t == token_type or token_instance == t.strip("'") for t in tokens):
                    return i + 1
        return -1
    
    def check_token_match(self, recognizer: Parser) -> bool:
        """
        Check if the current token matches the expected token from ATN transitions.
        First checks token type match, then falls back to literal value match.
        
        Args:
            recognizer: The parser instance to access token names and ATN

        Returns:
            bool: True if there is a mismatch, False if tokens match or no token expected
        """
        if not hasattr(self.state, 'transitions'):
            atn_state = recognizer._interp.atn.states[self.state]
        else:
            atn_state = self.state

        if not self.current_token:
            return False

        # Split token string into type and value
        token_str = str(self.current_token)
        token_type = token_str.split(" ")[0]  # e.g. "WORD" from "WORD ('Henricus')"

        if not atn_state.transitions:
            return False
        
        if self.node_type == "Rule exit":
            return False

        no_match = True
        for transition in atn_state.transitions:
            while transition.serializationType == 1:  # Epsilon transition
                next_state = transition.target
                if hasattr(next_state, "decision"): 
                    return False
                if not next_state.transitions:
                    return True
                transition = next_state.transitions[0]
                continue
            
            if not (transition.serializationType == 5 or transition.serializationType == 7):
                no_match = False
                break

            if isinstance(transition, AtomTransition):
                label = transition.label_

                # Get expected token name
                expected_token = recognizer.symbolicNames[label]

                if expected_token:
                    # Check for match
                    if expected_token == token_type:
                        no_match = False
                        break

            elif isinstance(transition, SetTransition):
                for t in transition.label:
                    expected_token = recognizer.symbolicNames[t]
                    if expected_token:
                        # Check for match
                        if expected_token == token_type:
                            no_match = False
                            break
            
        return no_match
    
    def to_dict(self):
        """
        Convert the node to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the node
        """
        return {
            "step_id": str(self.id),
            "node_type": self.node_type,
            "state": str(self.state),
            "current_token": str(self.current_token),
            "chosen": self.chosen_index,
            "input_text": self.input_text,
            "matching_error": self.matching_error,
            "possible_alternatives": str(self.possible_alternatives),
            "next_input_token": self.next_input_token,
            "next_input_literal": self.next_input_literal,
        }
