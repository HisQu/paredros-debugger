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

from antlr4 import ParserRuleContext
from antlr4.Parser import Parser
from paredros_debugger.CustomErrorHandler import CustomDefaultErrorStrategy

class CustomParser(Parser):
    """
    Enhanced Parser that tracks parsing events to build a traversal graph.
    Extends ANTLR's Parser class and delegates tracking to CustomDefaultErrorStrategy.
    """
    def __init__(self, input, output = ...):
        super().__init__(input, output)
        self._errHandler = CustomDefaultErrorStrategy()

    def enterRule(self, localctx:ParserRuleContext, state:int, ruleIndex:int):
        rule_name = self.ruleNames[ruleIndex]
        self._errHandler._handle_rule_entry(self, rule_name)
        super().enterRule(localctx, state, ruleIndex)

    def exitRule(self):
        rule_name = self.ruleNames[self._ctx.getRuleIndex()]
        self._errHandler._handle_rule_exit(self, rule_name)
        super().exitRule()

    def enterRecursionRule(self, localctx, state, ruleIndex, precedence):
        rule_name = self.ruleNames[ruleIndex]
        self._errHandler._handle_rule_entry(self, rule_name)
        super().enterRecursionRule(localctx, state, ruleIndex, precedence)

    def match(self, ttype):
        return super().match(ttype)
    
    def consume(self):
        t = self.getCurrentToken()
        self._errHandler._handle_token_consume(self, t)
        return super().consume()
