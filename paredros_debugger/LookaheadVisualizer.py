from antlr4 import *

class LookaheadVisualizer(ParserATNSimulator):
    def __init__(self, parser):
        super().__init__(parser, parser.atn, parser._interp.decisionToDFA, parser._interp.sharedContextCache)
        self.trace_atn_sim = True
        self.parser = parser
        self.lookahead_depth = 3  # How many tokens to show for lookahead

    def adaptivePredict(self, input, decision, outerContext):
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
