from paredros_debugger.CustomParser import CustomParser
# Generated from /home/patrick/DigitalHumanities/paredros-debugger/Samples/Simpleton/Simpleton_Reg.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,3,24,2,0,7,0,2,1,7,1,1,0,4,0,6,8,0,11,0,12,0,7,1,0,1,0,1,0,1,
        0,1,0,1,0,3,0,16,8,0,1,1,1,1,4,1,20,8,1,11,1,12,1,21,1,1,0,0,2,0,
        2,0,1,1,0,2,3,26,0,15,1,0,0,0,2,17,1,0,0,0,4,6,5,1,0,0,5,4,1,0,0,
        0,6,7,1,0,0,0,7,5,1,0,0,0,7,8,1,0,0,0,8,16,1,0,0,0,9,16,3,2,1,0,
        10,11,5,3,0,0,11,16,5,3,0,0,12,13,5,1,0,0,13,14,5,2,0,0,14,16,5,
        3,0,0,15,5,1,0,0,0,15,9,1,0,0,0,15,10,1,0,0,0,15,12,1,0,0,0,16,1,
        1,0,0,0,17,19,5,1,0,0,18,20,7,0,0,0,19,18,1,0,0,0,20,21,1,0,0,0,
        21,19,1,0,0,0,21,22,1,0,0,0,22,3,1,0,0,0,3,7,15,21
    ]

class Simpleton_RegParser ( CustomParser ):

    grammarFileName = "Simpleton_Reg.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'1'", "'2'", "'3'" ]

    symbolicNames = [ "<INVALID>", "EINS", "ZWEI", "DREI" ]

    RULE_startRule = 0
    RULE_zwoelf = 1

    ruleNames =  [ "startRule", "zwoelf" ]

    EOF = Token.EOF
    EINS=1
    ZWEI=2
    DREI=3

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class StartRuleContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EINS(self, i:int=None):
            if i is None:
                return self.getTokens(Simpleton_RegParser.EINS)
            else:
                return self.getToken(Simpleton_RegParser.EINS, i)

        def zwoelf(self):
            return self.getTypedRuleContext(Simpleton_RegParser.ZwoelfContext,0)


        def DREI(self, i:int=None):
            if i is None:
                return self.getTokens(Simpleton_RegParser.DREI)
            else:
                return self.getToken(Simpleton_RegParser.DREI, i)

        def ZWEI(self):
            return self.getToken(Simpleton_RegParser.ZWEI, 0)

        def getRuleIndex(self):
            return Simpleton_RegParser.RULE_startRule

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStartRule" ):
                listener.enterStartRule(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStartRule" ):
                listener.exitStartRule(self)




    def startRule(self):

        localctx = Simpleton_RegParser.StartRuleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_startRule)
        self._la = 0 # Token type
        try:
            self.state = 15
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 5 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 4
                    self.match(Simpleton_RegParser.EINS)
                    self.state = 7 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==1):
                        break

                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 9
                self.zwoelf()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 10
                self.match(Simpleton_RegParser.DREI)
                self.state = 11
                self.match(Simpleton_RegParser.DREI)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 12
                self.match(Simpleton_RegParser.EINS)
                self.state = 13
                self.match(Simpleton_RegParser.ZWEI)
                self.state = 14
                self.match(Simpleton_RegParser.DREI)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ZwoelfContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EINS(self):
            return self.getToken(Simpleton_RegParser.EINS, 0)

        def ZWEI(self, i:int=None):
            if i is None:
                return self.getTokens(Simpleton_RegParser.ZWEI)
            else:
                return self.getToken(Simpleton_RegParser.ZWEI, i)

        def DREI(self, i:int=None):
            if i is None:
                return self.getTokens(Simpleton_RegParser.DREI)
            else:
                return self.getToken(Simpleton_RegParser.DREI, i)

        def getRuleIndex(self):
            return Simpleton_RegParser.RULE_zwoelf

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterZwoelf" ):
                listener.enterZwoelf(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitZwoelf" ):
                listener.exitZwoelf(self)




    def zwoelf(self):

        localctx = Simpleton_RegParser.ZwoelfContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_zwoelf)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 17
            self.match(Simpleton_RegParser.EINS)
            self.state = 19 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 18
                _la = self._input.LA(1)
                if not(_la==2 or _la==3):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 21 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==2 or _la==3):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





