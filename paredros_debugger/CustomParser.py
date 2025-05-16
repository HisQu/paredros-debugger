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
        self._errHandler.traversal._add_new_node("Rule entry", self, rule_name)
        #self._errHandler.traversal._handle_parser_event("rule_entry", self, rule_name)
        super().enterRule(localctx, state, ruleIndex)

    def exitRule(self):
        rule_name = self.ruleNames[self._ctx.getRuleIndex()]
        self._errHandler.traversal._handle_parser_event("rule_exit", self, rule_name) 
        super().exitRule()

    def enterRecursionRule(self, localctx, state, ruleIndex, precedence):
        rule_name = self.ruleNames[ruleIndex]
        self._errHandler.traversal._handle_parser_event("rule_entry", self, rule_name)
        super().enterRecursionRule(localctx, state, ruleIndex, precedence)

    def match(self, ttype):
        return super().match(ttype)
    
    def consume(self):
        t = self.getCurrentToken()
        self._errHandler.traversal._handle_parser_event("token_consume", self, None, t)
        return super().consume()
