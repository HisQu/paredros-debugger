"""
CustomParser extends ANTLR's base Parser class to track parsing events during grammar processing.
It adds hooks into key parser operations to build a graph representation of the parsing process.

This class intercepts and logs:
- Rule entry/exit events
- Token consumption
- Recursive rule handling

The tracking is done by delegating to a CustomDefaultErrorStrategy which maintains the parse 
traversal graph. This allows visualizing how the parser moves through the grammar's ATN 
(Augmented Transition Network) while processing input.

Usage:
    The class is automatically used when ANTLR generates parser code, as the base Parser class
    gets replaced with CustomParser during parser generation.
"""
from antlr4 import TokenStream
from antlr4 import ParserRuleContext
from antlr4.Parser import Parser
from antlr4.atn import ParserATNSimulator
from paredros_debugger.CustomErrorHandler import CustomDefaultErrorStrategy

class CustomParser(Parser):
    """
    Enhanced Parser that tracks parsing events to build a traversal graph.
    Extends ANTLR's Parser class and delegates tracking to CustomDefaultErrorStrategy.
    """
    _interp: ParserATNSimulator

    def __init__(self, input: TokenStream, output = ...):
        super().__init__(input, output)
        self._errHandler = CustomDefaultErrorStrategy()
        self._errHandler.traversal.set_parser(self)

    def enterRule(self, localctx:ParserRuleContext, invokingState:int, ruleIndex:int):
        # Get the actual start ATN state object of the rule being entered
        actual_rule_start_state = self.atn.ruleToStartState[ruleIndex]
        
        self._errHandler.traversal.create_node(
            recognizer=self,
            node_type="Rule entry",
            event_rule_index=ruleIndex,
            event_atn_state_number=actual_rule_start_state.stateNumber 
        )
        super().enterRule(localctx, invokingState, ruleIndex)


    def exitRule(self):
        self._errHandler.traversal.create_node(self, "Rule exit")
        super().exitRule()

    def enterRecursionRule(self, localctx:ParserRuleContext, invokingState:int, ruleIndex:int, precedence:int):
        actual_rule_start_state = self.atn.ruleToStartState[ruleIndex]
        self._errHandler.traversal.create_node(
            recognizer=self,
            node_type="Rule entry",
            event_rule_index=ruleIndex,
            event_atn_state_number=actual_rule_start_state.stateNumber
        )
        super().enterRecursionRule(localctx, invokingState, ruleIndex, precedence)

    def match(self, ttype):
        return super().match(ttype)
    
    def consume(self):
        self._errHandler.traversal.create_node(self, "Token consume")
        return super().consume()
