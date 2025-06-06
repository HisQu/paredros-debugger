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

    def enterRule(self, localctx:ParserRuleContext, state:int, ruleIndex:int):
        rule_name = self.ruleNames[ruleIndex]
        if not self._errHandler.error_occurred:
            state = self._interp.atn.ruleToStartState[ruleIndex]
            # The state for the first rule is always -1 so we have to add a special case to account for that
            if self.state == -1: 
                self._errHandler.traversal._create_new_node("Rule entry", self, rule_name, None, state.stateNumber)
            # Every other rule has its normal statenumber and therefore doesnt need any special handling
            else:
                self._errHandler.traversal._create_new_node("Rule entry", self, rule_name, None)
        super().enterRule(localctx, state, ruleIndex)

    def exitRule(self):
        rule_name = self.ruleNames[self._ctx.getRuleIndex()]
        if not self._errHandler.error_occurred:
            self._errHandler.traversal._create_new_node("Rule exit", self, rule_name)
        super().exitRule()

    def enterRecursionRule(self, localctx, state, ruleIndex, precedence):
        rule_name = self.ruleNames[ruleIndex]
        if not self._errHandler.error_occurred:
            state = self._interp.atn.ruleToStartState[ruleIndex]
            if self.state == -1: 
                self._errHandler.traversal._create_new_node("Rule entry", self, rule_name, None, state.stateNumber)
            else:
                self._errHandler.traversal._create_new_node("Rule entry", self, rule_name, None)
        super().enterRecursionRule(localctx, state, ruleIndex, precedence)

    def match(self, ttype):
        return super().match(ttype)
    
    def consume(self):
        t = self.getCurrentToken()
        if not self._errHandler.error_occurred:
            self._errHandler.traversal._create_new_node("Token consume", self, t)
        return super().consume()
