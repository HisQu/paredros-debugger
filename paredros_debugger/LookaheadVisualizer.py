"""
LookaheadVisualizer extends ANTLR's ParserATNSimulator to track and visualize parser 
lookahead decisions. It intercepts the adaptive prediction process to record how the 
parser looks ahead in the token stream to resolve ambiguities.

The class captures:
- Current parsing context and state
- Lookahead tokens being examined
- Available transitions at decision points
- The chosen prediction path

This information is delegated to the CustomErrorStrategy's traversal graph to build
a complete picture of the parsing process.
"""

from antlr4 import *
from paredros_debugger.utils import copy_token_stream
from paredros_debugger.ParseTraversal import ParseTraversal

class LookaheadVisualizer(ParserATNSimulator):
    """
    Enhanced ATN simulator that tracks parser lookahead decisions.
    Extends ANTLR's ParserATNSimulator to intercept and log prediction operations.
    """
    def __init__(self, parser):
        super().__init__(parser, parser.atn, parser._interp.decisionToDFA, parser._interp.sharedContextCache)
        self.trace_atn_sim = True
        self.parser = parser
        self.lookahead_depth = 3  # How many tokens to show for lookahead

    def adaptivePredict(self, input, decision, outerContext):
        """
        Intercepts ANTLR's adaptive prediction to track lookahead decisions.
        Called by the parser when it needs to decide between multiple valid paths.
        Creates a new node in the parse traversal for each decision point.

        Args:
            input (TokenStream): The current token stream
            decision (int): The decision number in the parsing process
            outerContext (ParserRuleContext): The current rule context

        Returns:
            int: The chosen transition number

        Note:
            - Only tracks decisions if no error has occurred
            - Creates a Decision node in the traversal graph for each prediction
            - Sets the chosen transition based on ANTLR's prediction
        """
        if self.parser._errHandler.error_occurred:
            return super().adaptivePredict(input, decision, outerContext)

        # Perform prediction
        prediction = super().adaptivePredict(input, decision, outerContext)

         # Get current parsing context
        current_rule = self.parser.ruleNames[outerContext.getRuleIndex()] if outerContext else "start"
        
        traversal: ParseTraversal = self.parser._errHandler.traversal
        traversal._create_new_node("Decision", self.parser, current_rule, prediction)
        # Debug
        # ----------------------------------------
        # print(f"\n🔍 Decision point in {current_rule} (state {state} decision {decision})")
        # print(f"   Current token: {readableToken}")
        # print(f"   Lookahead ({self.lookahead_depth} tokens): {lookahead}")
        
        # # Get possible alternatives
        # if alternatives:
        #     print("   Possible alternatives:")
        #     for i, alt in enumerate(alternatives, 1):
        #         print(f"      {i}: Matches: {alt}")

        # print(f"   Chosen alternative: {prediction}")
        # print(f"   Input: {input_text}")
        # ----------------------------------------

        return prediction
