from typing import Optional, List
from collections import deque

from paredros_debugger.ParseTraceTree import ParseTraceTree, ParseTreeNode
from paredros_debugger.ParseStep import ParseStep
from paredros_debugger.ParseTraversal import ParseTraversal

class ParseTreeExplorer:
    """
    A parse explorer that maintains:
      - self.original_tree: the complete parse tree
      - self.working_tree: a partial parse tree up to max_work_id
      - self.current_step_id: the 'active' step
      - self.max_work_id: the highest step ID in self.working_tree

    Stepping logic:
      - If next_id <= max_work_id, we do a cut from the original tree. 
      - If next_id == max_work_id + 1, we handle expansions manually (like alt expansions).
      - If user tries to jump beyond that range, we error or skip.

    Decision = parseStep.possible_alternatives > 1.

    Alt expansions:
      - We call expand_alternatives() if the current step is a decision step.
      - We attach the new alt sub-tree nodes to the working_tree (no cut).
      - If the user chooses an alt, we set current_step_id to that alt's ID (which can be > max_work_id).
      - We do not re-cut because it is "manual" expansion beyond the original partial parse.
    """

    def __init__(self, full_tree: ParseTraceTree, traversal: ParseTraversal):
        # The final parse tree from the entire parse
        self.original_tree = full_tree

        # All steps from the parser's traversal
        self._traversal = traversal
        self._all_steps: List[ParseStep] = traversal.all_steps

        # We'll pick the largest ID from the original parse as our starting point 
        if self._all_steps:
            start_id = max(step.id for step in self._all_steps)
        else:
            start_id = 0

        self.current_step_id = start_id

        # Build the working_tree as a cut up to 'start_id'
        self.working_tree = self.original_tree.copy_and_cut(self.current_step_id)
        # compute max_work_id from the partial parse
        self.max_work_id = self._compute_max_work_id()

        # For alt expansions
        self._in_alternative_expansion_mode = False
        self._expanded_alt_nodes: List[ParseStep] = []
        self._expanded_alt_ptnodes: List[ParseTreeNode] = []

    # -------------------------------------------------------------------------
    # Basic & Utility
    # -------------------------------------------------------------------------
    def to_json(self) -> str:
        return self.working_tree.to_json(indent=2)

    def to_dict(self) -> dict:
        return self.working_tree.to_dict()

    def _compute_max_work_id(self) -> int:
        """Compute the maximum parse-step ID found in self.working_tree."""
        if not self.working_tree.root:
            return 0
        max_id = 0
        queue = deque([self.working_tree.root])
        while queue:
            node = queue.popleft()
            for st in node.trace_steps:
                if isinstance(st.id, int) and st.id > max_id:
                    max_id = st.id
            for c in node.children:
                queue.append(c)
        return max_id

    def _cut_to_step(self, step_id: int):
        """
        Rebuild self.working_tree by cutting from the original_tree up to `step_id`.
        Then recalc max_work_id.
        """
        self.working_tree = self.original_tree.copy_and_cut(step_id)
        self.max_work_id = self._compute_max_work_id()
        self.current_step_id = self.max_work_id

    @property
    def current_step(self) -> Optional[ParseStep]:
        """Get the current parse step (ParseStep) from the working tree."""
        return self._get_working_tree_step(self.current_step_id)

    # -------------------------------------------------------------------------
    # Step / Movement
    # -------------------------------------------------------------------------
    def step_forward(self, num_steps: int = 1):
        """
        Move forward num_steps from current_step_id. Each step means current_step_id+1.
        If that new ID <= max_work_id, we do a cut to that ID. 
        Else if it equals max_work_id+1, we handle alt expansions or an error if no alt available.
        """
        if num_steps < 1:
            return
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()  

        for _ in range(num_steps):
            next_id = self.current_step_id + 1
            # runtime error if we try to step further and we are at the end of the input
            # TODO: actually check input isntead of just step IDs
            if next_id > self.original_tree.last_step_id():
                raise RuntimeError("Cannot step beyond end of input.")

            # We are stepping beyond the current partial parse,
            # test if we are on the original path
            step = self.current_step
            if not step:
                raise RuntimeError(f"No parse step at ID={self.current_step_id} to expand from.")
            if step.chosen_index != -1:
                self._cut_to_step(next_id)
                return
            
            try:
                self.expand_alternatives()
                # if we have exactly one alt => auto choose
                if len(self._expanded_alt_nodes) == 1:
                    self.choose_alternative(1)
                # If we have multiple alts we need to pick one
                # We'll do no further auto stepping here.
            except:
                raise RuntimeError(f"No parse step at ID={self.current_step_id} to expand from.")
                # we are already at the last step! (no more alts)

    def go_back_one_step(self):
        """
        step back by exactly 1. If new_id <= max_work_id, do a cut. 
        If the old current_step_id was > max_work_id (meaning alt node),
        remove that alt node from the working tree.
        """
        if self.current_step_id <= 0:
            raise RuntimeError("Already at step 0; cannot go back further.")
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()

        new_id = self.current_step_id - 1
        
        # if new_id <= max_work_id => we do a cut
        if new_id <= self.max_work_id:
            self.current_step_id = new_id
            self._cut_to_step(new_id)
        elif self.current_step_id > self.max_work_id:
            # We were on an alt node => remove that alt from the tree
            self._remove_alt_step(self.current_step_id)
            self.current_step_id = new_id

    def reset_to_step_id(self, step_id: int):
        """
        Directly jump to step_id. If step_id <= max_work_id => do a cut.
        """
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()

        if step_id < 0:
            raise RuntimeError("Cannot reset to negative step ID.")

        if step_id > self.original_tree.last_step_id():
            raise RuntimeError(f"Step ID={step_id} is beyond the original parse.")

        self.current_step_id = step_id
        self._cut_to_step(step_id)

    def step_until_next_decision(self):
        """
        Repeatedly do step_forward(1) until we find a step with multiple alts or no more steps.
        We'll catch any errors if we try to exceed the parse range, etc.
        """
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()

        while True:
            cur_step = self.current_step
            if cur_step and len(cur_step.possible_alternatives) > 1:
                # already at a decision => break
                return
            # else step forward by 1
            try:
                self.step_forward(1)
            except RuntimeError:
                break  # can't step further => done

    def step_back_until_previous_decision(self):
        """
        Repeatedly go_back_one_step() until we find a step with multiple alts or reach 0.
        """
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()

        while self.current_step_id > 0:
            self.go_back_one_step()
            step = self.current_step
            if step and len(step.possible_alternatives) > 1:
                return
            
    # -------------------------------------------------------------------------
    # Alternative Expansion
    # -------------------------------------------------------------------------
    def expand_alternatives(self):
        """
        If the current step is a 'decision' (multiple possible_alternatives),
        create new alt steps with fresh IDs > max_orig_id, attach them to the working_tree.
        Then user can pick one or cancel. 
        
        This method simply takes the alternative nodes directly from ParseTraversal,
        and attaches them to the working tree.
        """
        if self._in_alternative_expansion_mode:
            self.cancel_alt_expansion()

        step = self.current_step
        # if len(step.possible_alternatives) < 2:
        #    raise RuntimeError("This step does not have multiple alternatives to expand.")

        # Find the parseTreeNode in the working_tree
        ptnode = self._find_ptnode_in_working(self.current_step_id)

        self._expanded_alt_nodes.clear()
        self._expanded_alt_ptnodes.clear()

        # Get alternatives for each possible choice in possible_alternatives
        possible_steps: list[ParseStep] = []
        for alt_index in range(len(step.possible_alternatives)):
            # Get the ParseStep for this alternative (alt_index is 0-based, method expects 1-based)
            alt_step = self._traversal.expand_alternative(step, alt_index + 1)
            if alt_step:
                possible_steps.append(alt_step)
            
        # Create ParseTreeNodes for each alternative and attach them to the working tree
        for idx, alt_step in enumerate(possible_steps):  
            # Create a new ParseTreeNode for this alternative
            alt_ptnode = ParseTreeNode(ruleName=alt_step.rule_name)
            alt_ptnode.trace_steps.append(alt_step)
                
            # Mark this as an alternative node
            if step.chosen_index and not idx+1 == step.chosen_index:
                alt_step.node_type = "alt_node"
            
            # Add this alternative ParseTreeNode as a child of the current ptnode
            ptnode.children.append(alt_ptnode)
            
            # Store the alternative nodes for later selection
            self._expanded_alt_nodes.append(alt_step)
            self._expanded_alt_ptnodes.append(alt_ptnode)

        self._in_alternative_expansion_mode = True

    def choose_alternative(self, alt_index: int):
        """
        Keep the chosen alt subtree, remove others, mark the chosen alt node_type as 'alt_chosen',
        and set current_step_id to that alt's ID (which now is > max_work_id).
        """
        if not self._in_alternative_expansion_mode:
            raise RuntimeError("Not in alt expansion mode.")

        if alt_index < 1 or alt_index > len(self._expanded_alt_nodes):
            raise RuntimeError(f"Invalid alt index {alt_index}, we have {len(self._expanded_alt_nodes)} expansions.")
        
        self._in_alternative_expansion_mode = False

        if alt_index == self.current_step.chosen_index:
            self.current_step_id += 1
            self._cut_to_step(self.current_step_id)
            return

        chosen_step = self._expanded_alt_nodes[alt_index - 1]
        chosen_pt   = self._expanded_alt_ptnodes[alt_index - 1]

        # remove other expansions
        for i, pt in enumerate(self._expanded_alt_ptnodes):
            if pt is not chosen_pt:
                self._remove_node_from_parent(self.working_tree.root, pt)

        # rename the chosen alt node
        chosen_step.node_type = "alt_chosen"

        self._expanded_alt_nodes.clear()
        self._expanded_alt_ptnodes.clear()
        self.current_step_id += 1
        chosen_step.id = self.current_step_id


    def cancel_alt_expansion(self):
        """Remove all alt expansions from the working_tree, remain at same step."""
        if not self._in_alternative_expansion_mode:
            return

        for pt in self._expanded_alt_ptnodes:
            self._remove_node_from_parent(self.working_tree.root, pt)

        self._expanded_alt_nodes.clear()
        self._expanded_alt_ptnodes.clear()
        self._in_alternative_expansion_mode = False

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _get_working_tree_step(self, step_id: int) -> Optional[ParseStep]:
        """
        Search the *working tree* for a parse step (ParseStep) whose .id == step_id.
        Returns the matching ParseStep, or None if not found.
        """
        if not self.working_tree or not self.working_tree.root:
            return None

        from collections import deque
        queue = deque([self.working_tree.root])

        while queue:
            node = queue.popleft()
            for st in node.trace_steps:
                if st.id == step_id:
                    return st
            for child in node.children:
                queue.append(child)

        return None

    def _find_ptnode_in_working(self, step_id: int) -> Optional[ParseTreeNode]:
        """BFS in the working_tree to find a node whose trace_steps contains step_id."""
        if not self.working_tree.root:
            return None
        queue = deque([self.working_tree.root])
        while queue:
            node = queue.popleft()
            for st in node.trace_steps:
                if st.id == step_id:
                    return node
            queue.extend(node.children)
        return None

    def _remove_node_from_parent(self, root: ParseTreeNode, target: ParseTreeNode) -> bool:
        """BFS to remove `target` from some node's children in working_tree."""
        queue = deque([root])
        while queue:
            cur = queue.popleft()
            for ch in list(cur.children):
                if ch is target:
                    cur.children.remove(ch)
                    return True
                else:
                    queue.append(ch)
        return False

    def _remove_alt_step(self, step_id: int):
        """
        BFS in working_tree to remove any parse-tree node whose first trace_step has ID=step_id,
        presumably an alt node if step_id > max_work_id.
        """
        if not self.working_tree.root:
            return
        queue = deque([self.working_tree.root])
        while queue:
            node = queue.popleft()
            for child in list(node.children):
                if child.trace_steps and child.trace_steps[0].id == step_id:
                    node.children.remove(child)
                    return
                queue.append(child)
