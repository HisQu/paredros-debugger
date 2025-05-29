from antlr4.Token import CommonToken, Token
from antlr4.Lexer import Lexer
from antlr4.error.Errors import LexerNoViableAltException
from antlr4.InputStream import InputStream
from typing import TextIO
import sys


class CustomLexer(Lexer):
    """Generated lexer plus INVALID-token support."""

    def __init__(self, input: InputStream, output: TextIO = sys.stdout):
        super().__init__(input, output)
        # ensures that the invalidtype never collides with a valid token type
        self.INVALID_TOKEN_TYPE = len(self.symbolicNames)

    def recover(self, e: LexerNoViableAltException):
        self.notifyListeners(e)

        start = self._tokenStartCharIndex
        stop  = self._input.index               
        tok = CommonToken(self._tokenFactorySourcePair,
                          self.INVALID_TOKEN_TYPE, 
                          Token.DEFAULT_CHANNEL,
                          start,
                          stop)
        
        # only emit the token if it is not just whitespace or a newline
        if not (tok.text == ' ' or tok.text == '\n'):
            self.emitToken(tok)                     
            self._type = self.INVALID_TOKEN_TYPE  # Use the instance variable

        self._input.consume()

    def returnInvalidTokenType(self):
        return self.INVALID_TOKEN_TYPE