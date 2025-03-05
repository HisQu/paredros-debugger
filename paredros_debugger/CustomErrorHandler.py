from antlr4.Token import Token
from antlr4.atn.ATNState import ATNState
from antlr4.error.Errors import RecognitionException, NoViableAltException, InputMismatchException, \
    FailedPredicateException, ParseCancellationException
from antlr4.atn.Transition import *
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
from antlr4.Parser import Parser

from paredros_debugger.ParseTraversal import ParseTraversal

Parser = None

class ErrorStrategy(object):

    def reset(self, recognizer:Parser):
        pass

    def recoverInline(self, recognizer:Parser):
        pass

    def recover(self, recognizer:Parser, e:RecognitionException):
        pass

    def sync(self, recognizer:Parser):
        pass

    def inErrorRecoveryMode(self, recognizer:Parser):
        pass

    def reportError(self, recognizer:Parser, e:RecognitionException):
        pass


class CustomDefaultErrorStrategy(DefaultErrorStrategy):

    def __init__(self):
        super().__init__()
        self.traversal = ParseTraversal()
        self.current_node = None
        self.error_occurred = False

    def reportError(self, recognizer:Parser, e:RecognitionException):
        print(f"ERROR type: {type(e)}")    
        # Only track first error
        if not self.error_occurred:  
            print(f"report called")
            self.error_occurred = True 
            
            # Create final error node to indicate where parsing failed
            state = recognizer._interp.atn.states[recognizer.state]
            rule = recognizer.ruleNames[recognizer._ctx.getRuleIndex()] if recognizer._ctx else "unknown"
            token = recognizer.getCurrentToken()
            lookahead = self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), 3)
            token_str = self._token_str(recognizer, token)
            alternatives = self.follow_transitions(state, recognizer)

            # Add final error node
            node = self.traversal.add_decision_point(
                state,
                token_str,
                lookahead,
                alternatives,
                self._get_consumed_tokens(recognizer.getTokenStream(), 3),
                rule,
                "Error"
            )
            node.set_error()

        super().reportError(recognizer, e)

    def recover(self, recognizer:Parser, e:RecognitionException):
        print(f"Recovering")
        print(f"[ErrorStrategy] Attempting recovery in state {recognizer.state} with token {e.offendingToken}")
        super().recover(recognizer, e)

    def sync(self, recognizer:Parser):
        # Only add states if no error occurred
        if self.error_occurred:
            return
        
        if not self.traversal.parser:
            self.traversal.set_parser(recognizer)

        # Attempt the same logging style as in adaptivePredict
        ruleIndex = recognizer._ctx.getRuleIndex() if recognizer._ctx else -1
        ruleName = recognizer.ruleNames[ruleIndex] if ruleIndex >= 0 else "unknown"
        state = recognizer._interp.atn.states[recognizer.state]
        currentToken = recognizer.getCurrentToken()
        readableToken = self._token_str(recognizer, currentToken)
        maxLookahead = 3

        # Debug
        # ---------------------------------------------------
        # print(f"\n🔍 Sync point in {ruleName} at state {state})")
        # print(f"   Current token: {readableToken}")

        # alternatives = self.follow_transitions(state, recognizer)
        
        # if alternatives:
        #     print("   Possible alternatives:")
        #     for i, alt in enumerate(alternatives, 1):
        #         print(f"      {i}: Matches: {alt}")

        # print(f"   Lookahead: {self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), maxLookahead)}")
        # print(f"   Consumed tokens: {self._get_consumed_tokens(recognizer.getTokenStream(), maxLookahead)}")
        # ---------------------------------------------------

        # Track sync point
        current_token = recognizer.getCurrentToken()
        lookahead = self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), maxLookahead)
        alternatives = self.follow_transitions(state, recognizer)
        input_text = self._get_consumed_tokens(recognizer.getTokenStream(), maxLookahead)

        # Create new decision point node
        node = self.traversal.add_decision_point(
            state,
            readableToken,
            lookahead,
            alternatives, 
            input_text,
            ruleName,
            "Sync"
        )

        # Check if the "last" node had a ruleentry that matches the current rule
        if self.current_node and self.current_node.possible_alternatives:
            if self.current_node.matches_rule_entry(ruleName):
                # Look for the alternative that matched the rule and mark it as chosen
                for i, (alt_state, tokens) in enumerate(self.current_node.possible_alternatives):
                    if any(t.startswith('Rule') and ruleName in t for t in tokens):
                        self.current_node.chosen = i + 1
                        break

        self.current_node = node

        super().sync(recognizer)

    def follow_transitions(self, state, recognizer, visited=None):
            # Necessary to avoid infinite recursion
            if visited is None:
                visited = set()
                    
            if state.stateNumber in visited:
                return []
                    
            visited.add(state.stateNumber)
            results = []

            # Rule stop special case
            if state.stateType == ATNState.RULE_STOP:
                results.append((state.stateNumber, ["Exit"]))
                return results

            for transition in state.transitions:
                # Create new visited set for each path
                path_visited = visited.copy()
                tokens = []

                # Handle atom transitions (single token)
                if isinstance(transition, AtomTransition):
                    # Hier nutzt man label_ anstatt label, danke fürs debuggen antlr
                    label = transition.label_
                    # First try symbolic names if literal is invalid
                    if (label < len(recognizer.literalNames) and 
                        recognizer.literalNames[label] == "<INVALID>" and 
                        label < len(recognizer.symbolicNames)):
                        tokens.append(recognizer.symbolicNames[label])
                    # Then try literal names
                    elif (label < len(recognizer.literalNames) and 
                        recognizer.literalNames[label]):
                        tokens.append(recognizer.literalNames[label])
                    # Finally fall back to symbolic names
                    elif (label < len(recognizer.symbolicNames) and 
                        recognizer.symbolicNames[label]):
                        tokens.append(recognizer.symbolicNames[label])
                    
                    if tokens:
                        results.append((state.stateNumber, tokens))
                        continue
                        
                # Handle set transitions (multiple tokens)
                elif isinstance(transition, SetTransition):
                    for t in transition.label:
                        # First try symbolic names if literal is invalid
                        if (t < len(recognizer.literalNames) and 
                            recognizer.literalNames[t] == "<INVALID>" and 
                            t < len(recognizer.symbolicNames)):
                            tokens.append(recognizer.symbolicNames[t])
                        # Then try literal names
                        elif (t < len(recognizer.literalNames) and 
                            recognizer.literalNames[t]):
                            tokens.append(recognizer.literalNames[t])
                        # Finally fall back to symbolic names
                        elif (t < len(recognizer.symbolicNames) and 
                            recognizer.symbolicNames[t]):
                            tokens.append(recognizer.symbolicNames[t])
                    
                    if tokens:
                        results.append((state.stateNumber, tokens))
                        continue

                # Handle rule transitions
                elif isinstance(transition, RuleTransition):
                    ruleName = recognizer.ruleNames[transition.ruleIndex] if transition.ruleIndex < len(recognizer.ruleNames) else "unknown"
                    results.append((transition.target.stateNumber, ["Rule " + ruleName]))
                    continue

                # Only follow epsilon transitions if we haven't found a match
                if not tokens:
                    next_results = self.follow_transitions(transition.target, recognizer, path_visited)
                    if next_results:
                        results.extend(next_results)

            return results

    # Helper functions
    # Returns the set of tokens that can follow the current state in the ATN
    def _get_lookahead_tokens(self, recognizer, input, lookahead_depth):
        tokens = []
        for i in range(1, lookahead_depth + 1):
            token = input.LT(i)
            if token.type == Token.EOF:
                break
            tokens.append(self._token_str(recognizer, token))
        return ", ".join(tokens)

    # Helper for getting one token as string
    def _token_str(self, recognizer, token):
        name = recognizer.symbolicNames[token.type]
        if name == "<INVALID>":
            return f"Literal ('{token.text}')"
        else:
            return f"{recognizer.symbolicNames[token.type]} ('{token.text}')"
        
    # Helper for getting the already consumed input 
    def _get_consumed_tokens(self, input, lookahead_depth):
        tokens = []
        for i in range(input.index):
            token = input.get(i)
            if token.type != Token.EOF:
                tokens.append(token.text)
        
        # How many tokens after the consumed tokens should be shown
        lookahead = []
        for i in range(1, lookahead_depth + 1):
            t = input.LT(i)
            if t and t.type != Token.EOF:
                lookahead.append(t.text)
        
        # Cursermarker for consumed tokens
        consumed = " ".join(tokens) + "⏺"
        if lookahead:
            consumed += " " + " ".join(lookahead)
            
        return consumed


    # called by the Parser upon a token match
    def _handle_token_consume(self, recognizer, token):
        if self.error_occurred:
            return
        
        state = recognizer._interp.atn.states[recognizer.state]
        maxLookahead = 3
        
        ruleIndex = recognizer._ctx.getRuleIndex() if recognizer._ctx else -1
        ruleName = recognizer.ruleNames[ruleIndex] if ruleIndex >= 0 else "unknown"
        token_str = self._token_str(recognizer, token)
        alternatives = self.follow_transitions(state, recognizer)

        # Update previous node if the current token matches an alternative
        if self.current_node and self.current_node.possible_alternatives:
            if self.current_node.matches_token(token_str):
                # We matched a token - mark it as chosen path
                self.current_node.chosen = self.current_node.get_matching_alternative(token_str)
        
        # creates a new node in the traversal 
        node = self.traversal.add_decision_point(
            state.stateNumber,
            token_str,
            self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), maxLookahead),
            alternatives,
            self._get_consumed_tokens(recognizer.getTokenStream(), maxLookahead),
            ruleName,
            "Token consume"
        )
        node.chosen = 1 # token matches are single pathed, the other cases are handled in sync
    
        
        self.current_node = node

    # called by the Parser upon a rule entry
    def _handle_rule_entry(self, recognizer, rule_name):
        """Handle rule entry and update decision tree"""
        if self.error_occurred:
            return
            
        # Only process if we have a previous node with no chosen alternative
        if self.current_node and self.current_node.chosen == -1:
            # Check if any alternative matches this rule entry
            for alt_idx, (target_state, tokens) in enumerate(self.current_node.possible_alternatives):
                if any(t.startswith(f'Rule {rule_name}') for t in tokens):
                    # Found matching rule - update chosen alternative
                    self.current_node.chosen = alt_idx + 1
                    break
                    
        # Create new node for the rule entry
        state = recognizer._interp.atn.states[recognizer.state]
        maxLookahead = 3
        alternatives = self.follow_transitions(state, recognizer)
        
        node = self.traversal.add_decision_point(
            state.stateNumber,
            rule_name,
            self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), maxLookahead),
            alternatives,
            self._get_consumed_tokens(recognizer.getTokenStream(), maxLookahead),
            rule_name,
            "Rule entry"
        )

        if len(alternatives) == 1:
            node.chosen = 1
        else: 
        # Look for exit alternative
            for alt_idx, (target_state, tokens) in enumerate(alternatives):
                if any(t == 'Exit' for t in tokens):
                    node.chosen = alt_idx + 1
                    break
            else:
                # No exit alternative found
                node.chosen = -1
        self.current_node = node
        

    # Das hier ist ein wenig missleading, da es für den aktuellen state die nachfolger bestimmt (nicht zwingend direkt der exit)
    # Es wäre besser wenn wir die alternativen für den nachfolger aufrufen oder einfach hardcoden dass es nur eine alternative (exit) gibt
    def _handle_rule_exit(self, recognizer, rule_name):
        """Handle rule exit and update decision tree"""
        if self.error_occurred:
            return
            
        if self.current_node and self.current_node.chosen == -1:
            # Check if any alternative matches this rule exit
            for alt_idx, (target_state, tokens) in enumerate(self.current_node.possible_alternatives):
                if any(t == 'Exit' for t in tokens):
                    # Found matching exit - update chosen alternative
                    self.current_node.chosen = alt_idx + 1
                    break

        # Create new node for the rule exit
        state = recognizer._interp.atn.states[recognizer.state]
        alternatives = self.follow_transitions(state, recognizer)
        node = self.traversal.add_decision_point(
            state.stateNumber,
            f"Rule exit: {rule_name}",
            self._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), 3),
            [(00, ['Exit'])],
            self._get_consumed_tokens(recognizer.getTokenStream(), 3),
            rule_name,
            "Rule exit"
        )
        node.chosen = 1
        self.current_node = node
                