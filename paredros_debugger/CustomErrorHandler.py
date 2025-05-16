"""
CustomErrorHandler.py

This module defines a custom error handling strategy for an ANTLR-based parser. It extends the 
default ANTLR error handling mechanism to integrate with a custom parse traversal system.

Classes:
    - ErrorStrategy: A base error handling strategy with placeholder methods.
    - CustomDefaultErrorStrategy: A subclass of DefaultErrorStrategy that implements custom 
      error reporting and handling.

Usage Example:
    To use the custom error strategy in an ANTLR parser:

        from antlr4.Parser import Parser
        from CustomErrorHandler import CustomDefaultErrorStrategy

        parser = Parser(...)
        parser._errHandler = CustomDefaultErrorStrategy()

Attributes:
    None
"""

from antlr4.Token import Token
from antlr4.atn.ATNState import ATNState
from antlr4.error.Errors import RecognitionException
from antlr4.atn.Transition import AtomTransition, SetTransition, RuleTransition
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
from antlr4.Parser import Parser

from paredros_debugger.ParseTraversal import ParseTraversal
from paredros_debugger.utils import copy_token_stream

# Parser = None

class ErrorStrategy(object):
    """
    A base error handling strategy with placeholder methods.
    """

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
    """
    A subclass of DefaultErrorStrategy that implements custom error reporting and handling.
    """

    def __init__(self):
        super().__init__()
        self.traversal = ParseTraversal()
        self.current_node = None
        self.error_occurred = False


    def reportError(self, recognizer:Parser, e:RecognitionException):
        """
        Enhance default Report Error and report an error to the parser and record the error in the parse traversal.

        Args:
            recognizer (Parser): The parser instance.
            e (RecognitionException): The recognition exception that occurred.

        Returns:
            None
        """
        print(f"ERROR type: {type(e)}")
        # Only track first error
        if not self.error_occurred:
            print(f"report called")
            self.error_occurred = True

            # # Create final error node to indicate where parsing failed
            # state = recognizer._interp.atn.states[recognizer.state]
            # rule = recognizer.ruleNames[recognizer._ctx.getRuleIndex()] if recognizer._ctx else "unknown"
            # token = recognizer.getCurrentToken()
            # lookahead = self.traversal._get_lookahead_tokens(recognizer, recognizer.getTokenStream(), 3)
            # token_str = self.traversal._token_str(recognizer, token)
            # alternatives = self.traversal.follow_transitions(state, recognizer)

            # # Add final error node
            # node = self.traversal.add_decision_point(
            #     state,
            #     token_str,
            #     lookahead,
            #     alternatives,
            #     self.traversal._get_consumed_tokens(recognizer.getTokenStream(), 3),
            #     rule,
            #     "Error",
            #     token_stream=copy_token_stream(recognizer.getTokenStream())
            # )
            # node.set_error()
            self.traversal._add_new_node("Error", recognizer)

        super().reportError(recognizer, e)

    def recover(self, recognizer:Parser, e:RecognitionException):
        """
        Enhance standard recovery and attempt to recover from a recognition exception with
        verbose logging.

        Args:
            recognizer (Parser): The parser instance.
            e (RecognitionException): The recognition exception that occurred.

        Returns:
            None
        """
        print("Recovering")
        print(f"[ErrorStrategy] Attempting recovery in state {recognizer.state} with token {e.offendingToken}")
        super().recover(recognizer, e)

    def sync(self, recognizer:Parser):
        """
        Enhance standard sync and attempt to synchronize the parser after a recognition exception
        with verbose logging.

        Args:
            recognizer (Parser): The parser instance.

        Returns:
            None
        """
        # Only add states if no error occurred
        if self.error_occurred:
            return

        # Attempt the same logging style as in adaptivePredict
        # ruleIndex = recognizer._ctx.getRuleIndex() if recognizer._ctx else -1
        # ruleName = recognizer.ruleNames[ruleIndex] if ruleIndex >= 0 else "unknown"
        # state = recognizer._interp.atn.states[recognizer.state]
        # currentToken = recognizer.getCurrentToken()
        # readableToken = self.traversal._token_str(recognizer, currentToken)
        # maxLookahead = 3

        # # Track sync point
        # current_token = recognizer.getCurrentToken()
        # lookahead = self.traversal._get_lookahead_tokens(recognizer, recognizer.getTokenStream(),
        #                                        maxLookahead)
        # alternatives = self.traversal.follow_transitions(state, recognizer)
        
        # input_text = self.traversal._get_consumed_tokens(recognizer.getTokenStream(), maxLookahead)

        # # Create new decision point node
        # node = self.traversal.add_decision_point(
        #     state,
        #     readableToken,
        #     lookahead,
        #     alternatives, 
        #     input_text,
        #     ruleName,
        #     "Sync",
        #     token_stream=copy_token_stream(recognizer.getTokenStream())
        # )

        # # Check if the "last" node had a ruleentry that matches the current rule
        # if self.current_node and self.current_node.possible_transitions:
        #     if self.current_node.matches_rule_entry(ruleName):
        #         # Look for the alternative that matched the rule and mark it as chosen
        #         for i, (_, tokens) in enumerate(self.current_node.possible_transitions):
        #             if any(t.startswith('Rule') and ruleName in t for t in tokens):
        #                 self.current_node.chosen_transition_index = i + 1
        #                 break

        # self.current_node = node
        self.traversal._add_new_node("Sync", recognizer)
        super().sync(recognizer)


