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
            self.traversal._create_new_node("Error", recognizer)

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

        self.traversal._create_new_node("Sync", recognizer)
        super().sync(recognizer)


