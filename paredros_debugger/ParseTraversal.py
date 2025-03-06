"""
ParseTraversal manages the construction and maintenance of a directed graph that represents 
the parser's path through the grammar. It tracks parser operations like:
- Decision points where multiple paths are possible
- Rule entries and exits
- Token consumption
- Alternative paths not taken

The graph structure consists of:
- Sequential nodes showing the actual parse path
- Alternative nodes showing other possible paths
- Merged nodes combining duplicate decision points

Key operations:
- Adding new decision points during parsing
- Expanding alternative paths on demand
- Merging duplicate decision sequences
- Managing node relationships and IDs
"""

from paredros_debugger.ParseNode import ParseNode

class ParseTraversal:
    def __init__(self):
        """
        Initialize a new parse traversal graph.

        Attributes:
            root (ParseNode): First node in the traversal
            current_node (ParseNode): Most recently added node
            all_nodes (list): Sequential list of all nodes in main path
            parser (Parser): Reference to parser instance for ATN access
        """
        self.root = None
        self.current_node = None
        self.all_nodes = []
        self.parser = None


    def set_parser(self, parser):
        """Set the parser instance"""
        self.parser = parser

    def add_decision_point(self, state, current_token, lookahead, possible_alternatives, input_text, current_rule, node_type):
        """
        Creates a new node in the parse traversal or updates an existing one. This method is called 
        by the parser at key points during parsing to track its progress through the grammar.

        The method handles duplicate nodes that can occur when both adaptivePredict and sync are
        called on the same state. In such cases, it updates the existing node instead of creating
        a new one.

        Args:
            state: Current ATN state number/object
            current_token: The token currently being processed
            lookahead: List of upcoming tokens being considered
            possible_alternatives: List of (state, tokens) pairs representing possible transitions
            input_text: Current input with cursor position showing progress
            current_rule: Name of the current grammar rule
            node_type: Type of node (Decision, Sync, Rule entry/exit, Token consume)

        Returns:
            ParseNode: Either a new node or the updated existing node

        Note:
            - Creates alternative nodes for each possible transition
            - Handles duplicate nodes from adaptivePredict and sync calls
            - Maintains the graph structure by linking nodes appropriately
            - Root node is set to first created node
        """
        if (self.current_node and 
            int(str(self.current_node.state)) == int(str(state)) and  
            self.current_node.chosen == -1):
            # Update current node
            self.current_node.possible_alternatives = possible_alternatives
            self.current_node.lookahead = lookahead
            self.current_node.input_text = input_text
            self.current_node.current_token = current_token
            self.current_node.rule_name = current_rule
            self.current_node.node_type = node_type
            return self.current_node

        # Create node if no duplicate found
        new_node = ParseNode(state, current_token, lookahead, possible_alternatives, input_text, current_rule, node_type)
        self.all_nodes.append(new_node)

        if not self.root:
            self.root = new_node
            self.current_node = new_node
        else:
            self.current_node.add_next_node(new_node)
            self.current_node = new_node

        if possible_alternatives:
            for alt_num, (target_state, tokens) in enumerate(possible_alternatives):
                alt_node = ParseNode(
                    target_state,
                    current_token,
                    lookahead,
                    [],  # No alternatives for alternative nodes yet
                    input_text,
                    current_rule,
                    node_type
                )
                new_node.add_alternative_node(alt_node)

        return new_node

    def expand_alternative(self, node, alternative_index):
        """Create a new branch from the given node for the specified alternative

        Args:
            node (ParseNode): The node containing the alternative to expand
            alternative_index (int): Index of the alternative to expand (1-based)

        Returns:
            ParseNode: The expanded alternative node with its new possible transitions
        """
        # Validate inputs
        if not node or alternative_index < 1 or alternative_index > len(node.alternative_nodes):
            return None

        # Get the alternative node we want to expand
        alt_node = node.alternative_nodes[alternative_index - 1]

        # Get target state from original node's possible alternatives
        target_state_num = node.possible_alternatives[alternative_index - 1][0]

        # Get the ATN state object
        target_state = self.parser._interp.atn.states[target_state_num]

        # Get possible transitions using the same method as in CustomErrorHandler
        possible_alternatives = self.parser._errHandler.follow_transitions(target_state, self.parser)

        # Update the alternative node with new transitions
        alt_node.possible_alternatives = possible_alternatives

        # Create child nodes for each possible transition
        if possible_alternatives:
            for target_state, tokens in possible_alternatives:
                child_node = ParseNode(
                    target_state,
                    alt_node.current_token,
                    alt_node.lookahead,
                    [],  # These nodes can be expanded further
                    alt_node.input_text,
                    alt_node.rule_name,
                    alt_node.node_type
                )
                alt_node.add_alternative_node(child_node)

        return alt_node

    def get_node_by_id(self, node_id):
        """Find a node by its unique identifier

        Args:
            node_id: The ID to search for (can be numeric or 'Alt X' format)

        Returns:
            ParseNode: The node with matching ID, or None if not found
        """
        def search_node(node):
            if str(node.id) == str(node_id):
                return node

            # Search alternative nodes
            for alt in node.alternative_nodes:
                if str(alt.id) == str(node_id):
                    return alt

            # Search next node in chain
            if node.next_node:
                result = search_node(node.next_node)
                if result:
                    return result

            return None

        if self.root:
            return search_node(self.root)
        return None

    def group_and_merge(self):
        """
        Identifies and merges duplicate decision/sync nodes to simplify the traversal graph.
        Only processes decision and sync nodes that share the same rule name and occur in sequence.

        Returns:
            list: Tuples of (original_nodes, merged_node) for each merged group

        Note:
            - Only merges nodes of type 'Decision' or 'Sync'
            - Ignores single nodes (no merge needed)
            - Preserves rule entry/exit and token consume nodes
        """
        # List to store groups of nodes that should be cleaned up
        cleanup_groups = []
        current_group = []
        current_rule = None

        for node in self.all_nodes:
            # Skip nodes we don't want to modify
            if node.node_type in ['Rule entry', 'Rule exit', 'Token consume']:
                # If we have a pending group, add it to cleanup_groups
                if len(current_group) > 1:
                    cleanup_groups.append(current_group)

                current_group = []
                current_rule = None    
                continue

            # Only process decision and sync nodes
            if node.node_type in ['Decision', 'Sync']:
                # If this is the start of a new group
                if not current_rule:
                    current_rule = node.rule_name
                    current_group = [node]
                # If this node belongs to current group
                elif node.rule_name == current_rule:
                    current_group.append(node)
                # If this node starts a new group
                else:
                    if len(current_group) > 1:  # Only add groups with multiple nodes
                        cleanup_groups.append(current_group)
                    current_group = [node]
                    current_rule = node.rule_name

        # Handle last group if exists
        if current_group and len(current_group) > 1:
            cleanup_groups.append(current_group)

        # Process each group and create merged nodes
        merged_nodes = []
        for group in cleanup_groups:
            # Get all unique alternatives from all nodes in group
            all_alternatives = set()
            for node in group:
                for target_state, matches in node.possible_alternatives:
                    all_alternatives.add((target_state, tuple(matches)))  # Convert list to tuple for set

            # Same logic as above but for alternative nodes
            seen_alt_nodes = set()
            all_alt_nodes = []
            for node in group:
                for alt_node in node.alternative_nodes:
                    # Use state as identifier since we dont need the same state twice
                    if alt_node.state not in seen_alt_nodes:
                        seen_alt_nodes.add(alt_node.state)
                        all_alt_nodes.append(alt_node)


            # Convert back to list and sort for consistency
            all_alternatives = sorted(list(all_alternatives))

            # Get the chosen alternative of the last node
            last_chosen = group[-1].chosen

            # If the last node had a chosen alternative, find its equivalent in merged alternatives
            # The last node always has a chosen alternative due to how we build our datastructure (we still double check for safety)
            new_chosen = -1
            if last_chosen > 0:
                last_node = group[-1]
                target_state, matches = last_node.possible_alternatives[last_chosen - 1]
                # Find matching alternative in merged set
                for i, (merged_state, merged_matches) in enumerate(all_alternatives):
                    if merged_state == target_state and tuple(matches) == merged_matches:
                        new_chosen = i + 1
                        break

            # Create merged node
            merged_node = ParseNode(
                state=group[0].state,  # Use first node's state
                current_token=group[-1].current_token,  # Use last node's token
                lookahead=group[-1].lookahead,  # Use last node's lookahead
                possible_alternatives=all_alternatives,  # Use merged alternatives
                input_text=group[-1].input_text,  # Use last node's input text
                rule=group[0].rule_name,  # Use rule name
                node_type="Merged " + group[0].node_type,  # Mark as merged
                parent_id=group[0].id - 1  # Use first node's parent ID
            )

            merged_node.id = group[0].id  # Use first node's ID
            merged_node.has_error = any(n.has_error for n in group)  # Mark as error if any node has error
            merged_node.alternative_nodes = all_alt_nodes  # Use all alternative nodes
            merged_node.chosen = new_chosen
            merged_nodes.append((group, merged_node))

        return merged_nodes


    def replace_merged_nodes(self, merged_groups):
        """
        Replaces groups of nodes with their merged versions and fixes the node structure.

        Args:
            merged_groups: List of tuples (original_group, merged_node) from group_and_merge()
        """

        # Create new list to rebuild in correct order
        new_nodes = []
        current_pos = 0

        for group, merged_node in merged_groups:
            # Add all nodes before the group
            while current_pos < len(self.all_nodes):
                node = self.all_nodes[current_pos]
                if node in group:
                    break
                new_nodes.append(node)
                current_pos += 1

            # Add merged node
            new_nodes.append(merged_node)

            # Update connections to merged node
            if new_nodes[-2:]:  # If we have at least 2 nodes
                prev_node = new_nodes[-2]
                prev_node.next_node = merged_node
                merged_node.parent = prev_node
            elif not new_nodes[:-1]:  # If this is the first node
                self.root = merged_node

            # Skip all nodes in group
            while current_pos < len(self.all_nodes) and self.all_nodes[current_pos] in group:
                if current_pos + 1 < len(self.all_nodes) and self.all_nodes[current_pos + 1] not in group:
                    # Connect merged node to the next node of the last node in the group
                    next_node = self.all_nodes[current_pos + 1]
                    merged_node.next_node = next_node
                    next_node.parent = merged_node
                current_pos += 1


        # Add any remaining nodes
        while current_pos < len(self.all_nodes):
            new_nodes.append(self.all_nodes[current_pos])
            current_pos += 1

        # Replace all_nodes with new ordered list
        self.all_nodes = new_nodes

        # Update root if needed
        if new_nodes:
            if not self.root:
                self.root = new_nodes[0]


    def _fix_node_ids(self):
        """
        Reassigns sequential IDs to all nodes in the traversal after structural changes.
        """
        next_id = 0

        # Fix IDs in all_nodes list to ensure sequential ordering
        for node in self.all_nodes:
            node.id = next_id
            next_id += 1

        # Fix IDs of alternative nodes for each node
        def update_alt(node):
            for i, alt in enumerate(node.alternative_nodes, 1):
                alt.id = f"Alt {i}"

            if node.next_node:
                update_alt(node.next_node)

        if self.root:
            update_alt(self.root)