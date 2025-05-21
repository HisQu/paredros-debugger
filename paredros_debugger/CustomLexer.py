from antlr4.Token import CommonToken, Token
from antlr4.Lexer import Lexer
from antlr4.error.Errors import LexerNoViableAltException


INVALID = 1000


class CustomLexer(Lexer):
    """Generated lexer plus INVALID-token support."""

    def recover(self, e: LexerNoViableAltException):
        self.notifyListeners(e)

        start = self._tokenStartCharIndex
        stop  = self._input.index               
        tok = CommonToken(self._tokenFactorySourcePair,
                          INVALID,
                          Token.DEFAULT_CHANNEL,
                          start,
                          stop)
        self.emitToken(tok)                     
        self._type = INVALID                    

        self._input.consume()
