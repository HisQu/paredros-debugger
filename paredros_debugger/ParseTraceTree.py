# paredros_debugger/ParseTraceTree.py
from paredros_debugger.ParseStep import ParseStep
from paredros_debugger.ParseTraversal import ParseTraversal
import json
from typing import List, Optional

class ParseTreeNode:
    """
    Either:
     - A 'rule' node (ruleName != None, token == None)
     - A 'token' node (token != None, ruleName == None)
    plus:
     - children (list of sub-rules or tokens)
     - trace_steps (list of 'ParseStep' for debugging)
     - a unique id to reference in the UI
    """

    _global_id_counter = 0

    def __init__(self, ruleName: Optional[str] = None, token: Optional[str] = None):
        self.rule_name = ruleName
        self.token = token
        self.children: List["ParseTreeNode"] = []
        self.trace_steps: List[ParseStep] = []  # list of 'ParseStep' references or copies

        # A unique ID for visualization (React Flow or anything else).
        self.id = f"ptn_{ParseTreeNode._global_id_counter}"
        ParseTreeNode._global_id_counter += 1

    def to_dict(self, verbose = False) -> dict:
        node_type = "token" if self.token else "rule"
        # if we find a faster way, maybe this information could be useful in the front end as well
        trace_info = []
        if verbose:
            for step in self.trace_steps:
                trace_info.append(step.to_dict())

        return {
            "id": self.id,
            "node_type": node_type,
            "rule_name": self.rule_name,
            "token": self.token,
            "trace_info": trace_info if verbose else "collapsed",
            "children": [child.to_dict(verbose) for child in self.children],
        }
    


class ParseTraceTree:
    """
    Reconstructs a grammar-based parse tree from 'ParseTraversal.all_steps' (the big chain
    of parse steps). Each node in this final tree is a 'ParseTreeNode' (either a rule or token).
    
    - We push a new rule node on 'Rule entry' and pop on 'Rule exit'.
    - Tokens become leaf nodes.
    - 'Decision', 'Sync', etc. parse nodes get stored as 'trace_steps' in the top-of-stack rule node.
    - The final result is a single root rule node with nested sub-rules/tokens in a clean tree,
      preserving the actual grammar structure (rather than the raw step-by-step chain).
    """

    def __init__(self):
        self.root: Optional[ParseTreeNode] = None
        self._traversal: ParseTraversal = None

        # for direct reference of steps by their id
        self.node_id_to_tree_node = {}

    def build_from_traversal(self, traversal: ParseTraversal):
        """
        Read 'traversal.all_steps' in order, building a grammar-based parse tree
        by pushing/popping rule nodes on a stack. We'll store references to the
        'ParseStep' objects inside the 'trace_steps' of each parse tree node.
        """
        if not traversal or not traversal.all_steps:
            return

        self._traversal = traversal
        stack: List[ParseTreeNode] = []

        for pnode in traversal.all_steps:
            nt = pnode.node_type

            if nt == "Rule entry":
                # We are entering a new grammar rule => create a new rule node
                rule_node = ParseTreeNode(ruleName=pnode.rule_name)
                rule_node.trace_steps.append(pnode)
                # Link to parent if any
                if stack:
                    stack[-1].children.append(rule_node)
                else:
                    self.root = rule_node
                stack.append(rule_node)

                # Also track in ID->tree_node for later direct reference
                self.node_id_to_tree_node[str(pnode.id)] = rule_node

            elif nt == "Token consume":
                token_node = ParseTreeNode(token=pnode.current_token)
                token_node.trace_steps.append(pnode)
                # Attach to the current rule on top of stack (if any)
                if stack:
                    stack[-1].children.append(token_node)
                else:
                    self.root = token_node

                # Track in ID->tree_node for later direct reference
                self.node_id_to_tree_node[str(pnode.id)] = token_node

            elif nt == "Rule exit":
                if stack:
                    top_rule_node = stack[-1]
                    top_rule_node.trace_steps.append(pnode)
                    stack.pop()

                # Record in ID->tree_node for later direct reference
                self.node_id_to_tree_node[str(pnode.id)] = top_rule_node

            else:
                # e.g. "Decision", "Sync", "Error"
                if stack:
                    stack[-1].trace_steps.append(pnode)

                # If there's no rule open, we might ignore or handle differently
                self.node_id_to_tree_node[str(pnode.id)] = stack[-1] if stack else None

    def copy_and_cut(self, max_step_id: int) -> "ParseTraceTree":
        """
        Produce a *new* ParseTraceTree that includes only those parse steps (and child nodes)
        whose step-IDs are <= `max_step_id`. Steps (and thus entire sub-nodes) with higher IDs
        are pruned out.

        Returns:
            ParseTraceTree: a freshly built partial copy.
        """
        if not self.root:
            return ParseTraceTree()

        # We’ll do a DFS from self.root, creating a parallel tree of ParseTreeNodes.
        new_tree = ParseTraceTree()

        def clone_node(old_node: ParseTreeNode) -> ParseTreeNode:
            # Filter out trace steps that have id <= max_step_id
            filtered_steps = [st for st in old_node.trace_steps if st.id <= max_step_id]

            # If no steps remain, we skip this node entirely.
            if not filtered_steps:
                return None

            # Create a new node with the same top-level fields (minus the children).
            new_node = ParseTreeNode(ruleName=old_node.rule_name, token=old_node.token)
            new_node.id = old_node.id 

            # Copy over the steps we kept
            new_node.trace_steps = filtered_steps

            # Recursively clone children
            new_children = []
            for child in old_node.children:
                cloned_child = clone_node(child)
                if cloned_child:
                    new_children.append(cloned_child)
            new_node.children = new_children

            return new_node

        # Build the new root
        new_root = clone_node(self.root)
        new_tree.root = new_root
        return new_tree

    def get_all_decision_steps(self, decision_types=None):
        """
        Return a list of 'decision steps' in this parse tree. By default, we consider
        node_type in ['Decision', 'Merged Decision', 'Sync', 'Merged Sync'] as 'decisions'.

        Each item in the returned list is a dict:
          {
            "step_id": str(step.id),
            "step_type": step.node_type,
            "owner_node_id": parseTreeNode.id,
            "owner_node_type": "rule" or "token",
            "ruleName": parseTreeNode.ruleName,
            "token": parseTreeNode.token,
          }

        The front end can iterate over these to highlight clickable decision points.
        """
        if decision_types is None:
            decision_types = ["Decision", "Merged Decision", "Sync", "Merged Sync"]

        results = []
        if not self.root:
            return results

        # Simple BFS or DFS to visit all parse-tree nodes
        queue = [self.root]
        while queue:
            ptnode = queue.pop(0)

            # Check each parse-step in this node
            for step in ptnode.trace_steps:
                if step.node_type in decision_types:
                    # Gather some info for the front end
                    item = {
                        "step_id": str(step.id),
                        "step_type": step.node_type,
                        "owner_node_id": ptnode.id,
                        "owner_node_type": "token" if ptnode.token else "rule",
                        "ruleName": ptnode.rule_name,
                        "token": ptnode.token,
                    }
                    results.append(item)

            # Enqueue children
            queue.extend(ptnode.children)

        return results
    
    def get_decision_step_by_id(self, step_id: str, decision_types=None):
        """
        Return a dict describing the 'decision' parse step with ID=step_id, if found.
        If not found or not in the allowed types, return None.
        """
        if decision_types is None:
            decision_types = ["Decision", "Merged Decision", "Sync", "Merged Sync"]

        if not self.root:
            return None

        queue = [self.root]
        while queue:
            ptnode = queue.pop(0)
            for step in ptnode.trace_steps:
                if str(step.id) == step_id and step.node_type in decision_types:
                    return {
                        "step_id": str(step.id),
                        "step_type": step.node_type,
                        "owner_node_id": ptnode.id,
                        "owner_node_type": "token" if ptnode.token else "rule",
                        "ruleName": ptnode.rule_name,
                        "token": ptnode.token,
                    }
            queue.extend(ptnode.children)

        return None
    
    def get_decision_node_and_step(self, step_id: str, decision_types=None):
        """
        If you also need direct references to (ParseTreeNode, ParseStep),
        not just a dict summary, you can do something like this:
        """
        if decision_types is None:
            decision_types = ["Decision", "Merged Decision", "Sync", "Merged Sync"]

        if not self.root:
            return None, None

        queue = [self.root]
        while queue:
            ptnode = queue.pop(0)
            for step in ptnode.trace_steps:
                if str(step.id) == step_id and step.node_type in decision_types:
                    return (ptnode, step)  # direct references
            queue.extend(ptnode.children)

        return None, None

    def to_dict(self, verbose:bool=False) -> dict:
        """Convert the entire parse tree to a dictionary (root + children)."""
        if not self.root:
            return {}
        return self.root.to_dict(verbose=verbose)

    def to_json(self, indent=2, verbose:bool=False) -> str:
        """Serialize the parse tree to JSON, optionally verbosely."""
        d = self.to_dict(verbose=verbose)
        return json.dumps(d, indent=indent, ensure_ascii=False)
    
    def last_step_id(self) -> int:
        """Return the highest step ID in the parse tree."""
        if not self.root:
            return 0
        return max(st.id for st in self._traversal.all_steps)

