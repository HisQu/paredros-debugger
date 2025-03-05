from antlr4 import ParseTreeListener

def resolveLiteralOrSymbolicName(parser, token):
    name = None
    if parser.symbolicNames:
        name = parser.symbolicNames[token.type]
    if name == "<INVALID>":
        return f"Literal: {token.text}"
    else:
        return f"{parser.symbolicNames[token.type]}: {token.text}"

class DetailedParseListener(ParseTreeListener):
    def __init__(self, parser):
        self.parser = parser
        self.indent = 0

    def enterEveryRule(self, ctx):
        rule = self.parser.ruleNames[ctx.getRuleIndex()]
        print(f"{'│ ' * self.indent}┌─ {rule}")
        self.indent += 1

    def exitEveryRule(self, ctx):
        self.indent -= 1
        rule = self.parser.ruleNames[ctx.getRuleIndex()]
        print(f"{'│ ' * self.indent}└─ {rule}")

    def visitTerminal(self, node):
        token = resolveLiteralOrSymbolicName(self.parser, node.getSymbol())
        print(f"{'│ ' * self.indent}├─ {token}")