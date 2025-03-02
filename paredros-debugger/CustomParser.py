from antlr4 import ParserRuleContext
from antlr4.Parser import Parser
from CustomErrorHandler import CustomDefaultErrorStrategy

class CustomParser(Parser):
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
