"""
ParseNode represents a node in the parser's traversal graph. Each node captures a specific point 
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
- alternative_nodes contain branching possibilities
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

class ParseNode:
    def __init__(self, state, current_token, lookahead, possible_alternatives, input_text, rule, node_type, parent_id=-1):
        """
        Initialize a new parse node.

        Args:
            state: ATN state number or object
            current_token: Current token being processed
            lookahead: List of upcoming tokens
            possible_alternatives: Available parsing alternatives as (state, tokens) pairs
            input_text: Current input context with cursor position
            rule: Current grammar rule name
            node_type: Type of node (Decision, Rule entry/exit, Token consume, Error)
            parent_id: ID of parent node for sequential numbering (-1 for root)
        """
        self.state = state                                  # ATN state number
        self.current_token = current_token                  # Current token being processed 
        self.lookahead = lookahead                          # List of upcoming tokens
        self.possible_alternatives = possible_alternatives  # Available parsing alternatives
        self.chosen = -1                                    # Chosen alternative (if known)
        self.input_text = input_text                        # Current input context
        self.next_node = None                               # Next node in the traversal sequence           
        self.next_node_verbose = None                       # Verbose representation of the next node
        self.parent = None                                  # Parent node
        self.alternative_nodes = []                         # Alternative nodes as siblings
        self.alternative_nodes_verbose = []                 # Verbose representation of the alternative nodes
        self.id = (parent_id + 1) if isinstance(parent_id, int) and parent_id >= 0 else 0  # Unique ID within its branch
        self.rule_name = rule                               # Current rule name
        self.has_error = False                              # Flag for error nodes
        self.node_type = node_type                          # Type of node (Decision, Rule, Token, Error)

    def add_next_node(self, next_node):
        """
        Add a sequential transition to the next node in the parse traversal.
        This represents the actual path taken during parsing.

        Args:
            next_node (ParseNode): The node to add as the next sequential step

        Note:
            - Sets bidirectional link between nodes (next_node and parent)
            - Updates the next node's ID to maintain sequential numbering
        """
        self.next_node = next_node
        next_node.parent = self
        next_node.id = self.id + 1

    def get_verbose_node(self):
        """Get the verbose representation of the next node"""
        if self.next_node is None:
            return None
        return f"state: {self.next_node.state}, rule_name: {self.next_node.rule_name}, node_type: {self.next_node.node_type}"

    def get_alternative_nodes_verbose(self):
        """Get the verbose representation of the possible alternatives"""
        for alternative in self.alternative_nodes:
            self.alternative_nodes_verbose.append(f"name: {alternative.rule_name}, state: {alternative.state}, tokens: {alternative.current_token}")
        return self.alternative_nodes_verbose

    def add_alternative_node(self, alt_node):
        """
        Add a branching alternative node representing a possible parse path.
        These nodes represent paths the parser could have taken but didn't.

        Args:
            alt_node (ParseNode): The node representing an alternative parse path

        Note:
            - Alternative nodes get IDs like "Alt 1", "Alt 2" etc.
            - Sets parent link back to this node
        """
        self.alternative_nodes.append(alt_node)
        alt_node.parent = self
        alt_node.id = "Alt " + str(len(self.alternative_nodes))

    def get_unique_identifier(self):
        """Get unique identifier combining ID and state"""
        return f"{self.id}"

    def set_error(self):
        """Mark this node as having an error"""
        self.has_error = True

    def print_attributes(self):
        """Pretty Print the object's attributes."""
        self.next_node_verbose = self.get_verbose_node()
        self.alternative_nodes_verbose = self.get_alternative_nodes_verbose()
        pprint(vars(self))

    def get_attributes_next_node(self):
        """Returns the object's attributes as a dictionary."""
        return json.dumps(vars(self.next_node), indent=4)

    def get_attributes_as_json(self):
        """Returns the object's attributes as a JSON string."""
        return json.dumps(vars(self), indent=4)

    def follow_path_to_tokens(self, recognizer, visited_rules=None):
        """
        Follow transitions from a specific state until finding token transitions.

        Args:
            recognizer: The parser instance
            start_state_id: The ATN state ID to start from
            visited_rules: Set of already visited rule names (for recursion breaking)

        Returns:
            list: token_transitions as list of (state_number, tokens) for atom/set transitions
        """
        if visited_rules is None:
            visited_rules = set()

        # Array of reachable tokens
        token_transitions = []

        # Prevent crash for calling function on consume nodes
        if hasattr(self.state, 'stateNumber'):
            states_to_visit = [self.state.stateNumber]
        else:
            states_to_visit = [self.state]
 

        while states_to_visit:
            # Process next state in the queue
            current_state = states_to_visit.pop(0)

            # Get the ATN state
            atn_state = recognizer._interp.atn.states[current_state]

            for transition in atn_state.transitions:
                tokens = []

                # Handle atom transitions
                if isinstance(transition, AtomTransition):
                    label = transition.label_

                    # Try symbolic names if literal is invalid
                    if (label < len(recognizer.literalNames) and 
                        recognizer.literalNames[label] == "<INVALID>" and 
                        label < len(recognizer.symbolicNames)):
                        tokens.append(recognizer.symbolicNames[label])
                    # Try literal names
                    elif (label < len(recognizer.literalNames) and 
                        recognizer.literalNames[label]):
                        tokens.append(recognizer.literalNames[label])
                    # Fall back to symbolic names
                    elif (label < len(recognizer.symbolicNames) and 
                        recognizer.symbolicNames[label]):
                        tokens.append(recognizer.symbolicNames[label])

                    if tokens:
                        token_transitions.append((current_state, tokens))
                        continue

                # Handle set transitions
                elif isinstance(transition, SetTransition):
                    for t in transition.label:
                        # Try symbolic names if literal is invalid
                        if (t < len(recognizer.literalNames) and 
                            recognizer.literalNames[t] == "<INVALID>" and 
                            t < len(recognizer.symbolicNames)):
                            tokens.append(recognizer.symbolicNames[t])
                        # Try literal names
                        elif (t < len(recognizer.literalNames) and 
                            recognizer.literalNames[t]):
                            tokens.append(recognizer.literalNames[t])
                        # Fall back to symbolic names
                        elif (t < len(recognizer.symbolicNames) and 
                            recognizer.symbolicNames[t]):
                            tokens.append(recognizer.symbolicNames[t])

                    if tokens:
                        token_transitions.append((current_state, tokens))
                        continue

                # Handle rule transitions
                elif isinstance(transition, RuleTransition):
                    rule_name = recognizer.ruleNames[transition.ruleIndex] if transition.ruleIndex < len(recognizer.ruleNames) else "unknown"

                    # Skip if we've seen this rule before
                    if rule_name in visited_rules:
                        continue

                    visited_rules.add(rule_name)
                    states_to_visit.append(transition.target.stateNumber)
                    continue

                # For epsilon transitions, just add the target state
                else:
                    states_to_visit.append(transition.target.stateNumber)

        return token_transitions

    def matches_rule_entry(self, ruleName):
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

    def matches_token(self, token_str):
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

    def get_matching_alternative(self, token_str):
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
