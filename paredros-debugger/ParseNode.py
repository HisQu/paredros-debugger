from pprint import pprint
import json

class ParseNode:
    def __init__(self, state, current_token, lookahead, possible_alternatives, input_text, rule, node_type, parent_id=-1):
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
        self.has_error = False
        self.node_type = node_type

    def add_next_node(self, next_node):
        """Add the next node in the traversal sequence"""
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
        """Add a node representing an alternative parse path"""
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
        self.next_node_verbose = self.get_verbose_node()
        self.alternative_nodes_verbose = self.get_alternative_nodes_verbose()
        pprint(vars(self))

    def get_attributes_next_node(self):
        """Returns the object's attributes as a dictionary."""
        return json.dumps(vars(self.next_node), indent=4)

    def get_attributes_as_json(self):
        """Returns the object's attributes as a JSON string."""
        return json.dumps(vars(self), indent=4)
    
    # Helper methods for checking if a node matches the current rule or token
    # These methods check all alternatives and return True if any match
    # This way we can determine the alternative for nodes that have no chosen given

    def matches_rule_entry(self, ruleName):
        """Check if this node represents entry into the given rule"""
        for alt_state, tokens in self.possible_alternatives:
            if any(t.startswith('Rule') and ruleName in t for t in tokens):
                return True
        return False

    # Helper method for checking if a node matches the current token, called by the error handler
    def matches_token(self, token_str):
        """Check if this node matches a given token"""
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
    
    # Helper method for getting the index of the alternative that matches the token, called by the error handler
    def get_matching_alternative(self, token_str):
        """Get the index of the alternative that matches the token"""
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
