"""
LookaheadVisualizer extends ANTLR's ParserATNSimulator to track and visualize parser 
lookahead decisions. It intercepts the adaptive prediction process to record how the 
parser looks ahead in the token stream to resolve ambiguities.

The class captures:
- Current parsing context and state
- Lookahead tokens being examined
- Available alternatives at decision points
- The chosen prediction path

This information is delegated to the CustomErrorStrategy's traversal graph to build
a complete picture of the parsing process.
"""

from antlr4 import *

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
            int: The chosen alternative number

        Note:
            - Only tracks decisions if no error has occurred
            - Creates a Decision node in the traversal graph for each prediction
            - Sets the chosen alternative based on ANTLR's prediction
        """
        if self.parser._errHandler.error_occurred:
            return super().adaptivePredict(input, decision, outerContext)
        
        # Get current parsing context
        current_rule = self.parser.ruleNames[outerContext.getRuleIndex()] if outerContext else "start"

        # Perform prediction
        prediction = super().adaptivePredict(input, decision, outerContext)

        # Show lookahead information
        current_token = input.LT(1)
        lookahead = self.parser._errHandler._get_lookahead_tokens(self.parser, input, self.lookahead_depth)
        state = self.parser.state
        atn_state = self.parser._interp.atn.states[state]
        readableToken = self.parser._errHandler._token_str(self.parser, current_token)
        input_text = self.parser._errHandler._get_consumed_tokens(input, self.lookahead_depth)
        alternatives = self.parser._errHandler.follow_transitions(atn_state, self.parser)
        
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

        node = self.parser._errHandler.traversal.add_decision_point(
            state,
            readableToken,
            lookahead,
            alternatives,
            input_text, 
            current_rule,
            "Decision"
            )
        node.chosen = prediction

        return prediction
