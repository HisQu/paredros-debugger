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
from antlr4.atn.Transition import AtomTransition, SetTransition, RuleTransition
from antlr4.atn.ATNState import ATNState

from paredros_debugger.ParseStep import ParseStep
from paredros_debugger.utils import copy_token_stream

class ParseTraversal:
    def __init__(self):
        """
        Initialize a new parse traversal graph.

        Attributes:
            root (ParseNode): First node in the traversal
            current_node (ParseNode): Most recently added node
            all_steps (list): Sequential list of all nodes in main path
            parser (Parser): Reference to parser instance for ATN access
        """
        self.root: ParseStep = None
        self.current_node: ParseStep = None
        self.all_steps : list[ParseStep] = []
        self.parser = None


    def set_parser(self, parser):
        """Set the parser instance"""
        self.parser = parser

    def follow_transitions(self, state, recognizer = None, visited=None):
        """
        Traverses the ATN (Augmented Transition Network) starting from a given state
        and collects all possible transitions.

        This used to live in CustomDefaultErrorStrategy, but now is central to
        ParseTraversal. We call it anywhere we need to get the “possible” transitions
        from an ATN state.

        Args:
            state (ATNState): The current ATN state.
            recognizer (Parser): The parser instance.
            visited (set): A set of visited states to avoid infinite recursion.

        Returns:
            list: A list of possible transitions, e.g. [(stateNumber, [tokens])]
        """
        if not recognizer:
            recognizer = self.parser

        if visited is None:
            visited = set()

        # Avoid infinite recursion
        if state.stateNumber in visited:
            return []

        visited.add(state.stateNumber)
        results = []

        # If this is a rule-stop state, return 'Exit'
        if state.stateType == ATNState.RULE_STOP:
            results.append((state.stateNumber, ["Exit"]))
            return results

        for transition in state.transitions:
            path_visited = visited.copy()
            tokens = []
            next_state = state.stateNumber

            # -- AtomTransition => single token
            if isinstance(transition, AtomTransition):
                label = transition.label_
                # Convert label to its symbolicName
                symbolic = recognizer.symbolicNames[label] if label < len(recognizer.symbolicNames) else None
                if symbolic:
                    results.append((next_state, symbolic))
                continue

            # -- SetTransition => multiple tokens
            elif isinstance(transition, SetTransition):
                set_tokens = []
                for t in transition.label:
                    if t < len(recognizer.symbolicNames):
                        set_tokens.append(recognizer.symbolicNames[t])
                results.append((next_state, set_tokens))
                continue

            # -- RuleTransition => calls sub-rule
            elif isinstance(transition, RuleTransition):
                rule_index = transition.ruleIndex
                rule_name = recognizer.ruleNames[rule_index] if rule_index < len(recognizer.ruleNames) else "unknown"
                results.append((next_state, [f"Rule {rule_name}"]))
                continue

            # Epsilon transitions => keep searching
            if not tokens:
                next_results = self.follow_transitions(transition.target, recognizer, path_visited)
                if next_results:
                    results.extend(next_results)

        return results

    def follow_path_to_tokens(self, start_state, recognizer=None, visited_rules=None):
        """
        Performs a full expansion of all 'Rule xyz' placeholders, returning only actual tokens.

        Args:
            start_state: (int or ATN state object) The initial ATN state to explore.
            recognizer: (Parser) If None, defaults to self.parser.
            visited_rules: (set) For recursion avoidance, if needed.

        Returns:
            A list of (stateNumber, [TOKENS...]) with no 'Rule ...' placeholders left.
        """
        if recognizer is None:
            recognizer = self.parser
        if visited_rules is None:
            visited_rules = set()

        # Step 1: get the first-level transitions
        initial = self.follow_transitions(start_state, recognizer=recognizer)
        # e.g. [(12, ['Rule expr']), (13, ['INT']), (14, ['Exit'])...]

        expanded = []
        queue = list(initial)

        while queue:
            state_num, tokens = queue.pop(0)

            # Partition this item’s tokens into real tokens vs. 'Rule X' placeholders
            rule_names = [t for t in tokens if t.startswith("Rule ")]
            pure_tokens = [t for t in tokens if not t.startswith("Rule ")]

            # If no rule placeholders, we can finalize this item
            if not rule_names:
                expanded.append((state_num, pure_tokens))
                continue

            # Otherwise, put any real tokens in 'expanded'
            if pure_tokens:
                expanded.append((state_num, pure_tokens))

            # Expand each rule placeholder
            for rule_tok in rule_names:
                # rule_tok looks like "Rule expr", so parse out the rule name
                rule_name = rule_tok.split(" ", 1)[1]  # "expr"

                # If we've visited this rule, skip (optional)
                if rule_name in visited_rules:
                    continue
                visited_rules.add(rule_name)

                # Find the rule index => rule start state => gather subresults
                if rule_name in recognizer.ruleNames:
                    rule_idx = recognizer.ruleNames.index(rule_name)
                    rule_start = recognizer.atn.ruleToStartState[rule_idx]

                    subres = self.follow_path_to_tokens(rule_start, recognizer, visited_rules)
                    # subres is also [(stateNum, [tokens])]
                    # Add them to the queue to further expand
                    queue.extend(subres)

        return expanded

    def add_decision_point(self, state, current_token, lookahead, possible_alternatives, input_text, current_rule, node_type, token_stream):
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
            self.current_node.chosen_index == -1):
            # Update current node
            self.current_node.possible_alternatives = possible_alternatives
            self.current_node.lookahead = lookahead
            self.current_node.input_text = input_text
            self.current_node.current_token = current_token
            self.current_node.rule_name = current_rule
            self.current_node.node_type = node_type
            self.current_node.token_stream = token_stream
            return self.current_node

        # Create node if no duplicate found
        new_node = ParseStep(state, current_token, lookahead, possible_alternatives, input_text, current_rule, node_type, token_stream)
        self.all_steps.append(new_node)

        if not self.root:
            self.root = new_node
            self.current_node = new_node
        else:
            self.current_node.add_next_node(new_node)
            self.current_node = new_node

        if possible_alternatives:
            for alt_num, (target_state, tokens) in enumerate(possible_alternatives):

                state = self.parser._interp.atn.states[target_state]
                rule_index = state.ruleIndex if hasattr(state, "ruleIndex") else -1
                rule_name = self.parser.ruleNames[rule_index] if rule_index >= 0 else "unknown"

                alt_node = ParseStep(
                    target_state,
                    current_token,
                    lookahead,
                    [],  # No alternatives for alternative nodes yet
                    input_text,
                    rule_name,
                    node_type,
                    token_stream
                )
                alt_node.matching_error = alt_node.check_token_match(self.parser)
                new_node.add_alternative_node(alt_node)
        
        new_node.matching_error = new_node.check_token_match(self.parser)

        return new_node

    def expand_alternative(self, node: ParseStep, alternative_index: int):
        """Create a new branch from the given node for the specified alternative

        Args:
            node (ParseStep): The node containing the alternative to expand
            alternative_index (int): Index of the alternative to expand (1-based)

        Returns:
            ParseStep: The expanded alternative node with its new possible transitions
        """
        if not node or alternative_index < 1 or alternative_index > len(node.next_node_alternatives):
            return None

        # Get the state of the node we want to expand
        alt_node = node.next_node_alternatives[alternative_index - 1]
        target_state_num = node.possible_alternatives[alternative_index - 1][0]
        target_state = self.parser._interp.atn.states[target_state_num]

        # Get all possible transitions and update node
        possible_alternatives = self.follow_transitions(
            target_state.transitions[0].target, self.parser
        )
        alt_node.possible_alternatives = possible_alternatives

        # Create child nodes for each possible transition
        if possible_alternatives:
            for new_target_state, token in possible_alternatives:

                state = self.parser._interp.atn.states[new_target_state]
                rule_index = state.ruleIndex if hasattr(state, "ruleIndex") else -1
                rule_name = self.parser.ruleNames[rule_index] if rule_index >= 0 else "unknown"

                child_node = ParseStep(
                    new_target_state,
                    alt_node.current_token,
                    alt_node.lookahead,
                    [],  # These nodes can be expanded further
                    alt_node.input_text,
                    rule_name,
                    alt_node.node_type,
                    token_stream=copy_token_stream(alt_node.token_stream)
                )
                if token in self.parser.symbolicNames:
                    # match check
                    child_node.matching_error = (alt_node.current_token != token)
                    # consume token manually
                    child_node.token_stream.consume()
                    next_token = child_node.token_stream.tokens[child_node.token_stream.index]
                    child_node.current_token = self.parser.symbolicNames[next_token.type]
                    child_node.input_text = self.parser._errHandler._get_consumed_tokens(child_node.token_stream, 3)
                    child_node.lookahead = self.parser._errHandler._get_lookahead_tokens(self.parser, child_node.token_stream, 3)
                    # debug info for next token
                    if child_node.token_stream.index < len(child_node.token_stream.tokens):
                        # the next lookahead token
                        upcoming_token = child_node.token_stream.LT(1)
                        child_node.next_input_token = self.parser.symbolicNames[upcoming_token.type]
                        child_node.next_input_literal = upcoming_token.text
                    else:
                        child_node.next_input_token = None
                        child_node.next_input_literal = None

                alt_node.add_alternative_node(child_node)

            alt_node.matching_error = alt_node.check_token_match(self.parser)

        return alt_node

    def get_node_by_id(self, node_id) -> ParseStep :
        """Find a node by its unique identifier

        Args:
            node_id: The ID to search for (can be numeric or 'Alt X' format)

        Returns:
            ParseNode: The node with matching ID, or None if not found
        """
        def search_node(node: ParseStep):
            if str(node.id) == str(node_id):
                return node

            # Search alternative nodes
            for alt in node.next_node_alternatives:
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
        cleanup_groups: list[list[ParseStep]] = []
        current_group: list[ParseStep] = []
        current_rule = None

        for node in self.all_steps:
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
                for alt_node in node.next_node_alternatives:
                    # Use state as identifier since we dont need the same state twice
                    if alt_node.state not in seen_alt_nodes:
                        seen_alt_nodes.add(alt_node.state)
                        all_alt_nodes.append(alt_node)


            all_alternatives = sorted(list(all_alternatives))
            last_chosen = group[-1].chosen_index

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
            merged_node = ParseStep(
                state=group[0].state, 
                current_token=group[-1].current_token,  
                lookahead=group[-1].lookahead,  
                possible_alternatives=all_alternatives,  
                input_text=group[-1].input_text,  
                rule=group[0].rule_name,  
                node_type="Merged " + group[0].node_type,
                token_stream=group[0].token_stream,
                parent_id=group[0].id - 1  
            )

            merged_node.id = group[0].id  # Use first node's ID
            merged_node.has_error = any(n.has_error for n in group)  # Mark as error if any node has error
            merged_node.next_node_alternatives = all_alt_nodes  # Use all alternative nodes
            merged_node.chosen_index = new_chosen
            merged_nodes.append((group, merged_node))

        return merged_nodes


    def replace_merged_nodes(self, merged_groups: list[tuple[list[ParseStep], ParseStep]]):
        """
        Replaces groups of nodes with their merged versions and fixes the node structure.
        """
        new_nodes = []
        current_pos = 0

        for group, merged_node in merged_groups:
            # Add all nodes before the group
            while current_pos < len(self.all_steps):
                node = self.all_steps[current_pos]
                if node in group:
                    break
                new_nodes.append(node)
                current_pos += 1

            # Add merged node and update connections
            new_nodes.append(merged_node)
            
            # Connect to previous node
            if len(new_nodes) > 1:
                prev_node = new_nodes[-2]
                prev_node.next_node = merged_node
                merged_node.parent = prev_node

            # Skip nodes in group
            while current_pos < len(self.all_steps) and self.all_steps[current_pos] in group:
                current_pos += 1

            # Connect to next node after group
            if current_pos < len(self.all_steps):
                next_node = self.all_steps[current_pos]
                merged_node.next_node = next_node
                next_node.parent = merged_node

            # Transfer alternative nodes and their relationships
            merged_node.next_node_alternatives = group[-1].next_node_alternatives
            for alt_node in merged_node.next_node_alternatives:
                alt_node.parent = merged_node

        # Add remaining nodes
        while current_pos < len(self.all_steps):
            new_nodes.append(self.all_steps[current_pos])
            current_pos += 1

        self.all_steps = new_nodes
        
        # Update root if needed
        if new_nodes:
            self.root = new_nodes[0]
            self.root.parent = None


    def _fix_node_ids(self):
        """
        Reassigns sequential IDs to all nodes in the traversal after structural changes.
        """
        next_id = 0

        # Fix IDs in steps list to ensure sequential ordering
        for node in self.all_steps:
            node.id = next_id
            next_id += 1

        # Fix IDs of alternative nodes for each node
        def update_alt(node: ParseStep):
            for i, alt in enumerate(node.next_node_alternatives, 1):
                alt.id = str(node.id) + "." + str(i)

            if node.next_node:
                update_alt(node.next_node)

        if self.root:
            update_alt(self.root)