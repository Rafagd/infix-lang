from dataclasses import dataclass
from enum import Enum, auto

from util import can_convert_to

class TokenType(Enum):
    UNKNOWN    = auto()
    IDENTIFIER = auto()
    BRACKET    = auto()
    NULL       = auto()
    BOOLEAN    = auto()
    INTEGER    = auto()
    FLOAT      = auto()
    STRING     = auto()

@dataclass
class Token:
    kind:  TokenType = TokenType.UNKNOWN
    value: str       = ''
    row:   int       = 0
    col:   int       = 0

class Tokenizer:
    def __init__(self, source):
        self.source = source

    def __iter__(self):
        self.row    = 1
        self.col    = 1
        self.cursor = self.second_pass()
        return self

    def __next__(self):
        return next(self.cursor);

    def first_pass(self):
        parsing     = False
        ptype       = 0
        token       = ''
        token_row   = 1
        token_col   = 1

        for c in self.source:
            if c == '\n':
                self.row += 1
                self.col  = 0
                if parsing and ptype == 2:
                    parsing = False
                    ptype   = 0
                    token   = ''

            if not parsing and c.isspace():
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                token_row = self.row
                token_col = self.col + 1
            
            elif not parsing and c in [ ',', ';' ]:
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                yield Token(kind=TokenType.IDENTIFIER, value=c, row=self.row, col=self.col)
                token_row = self.row
                token_col = self.col + 1

            elif not parsing and c in [ '{', '(', '[', ']', ')', '}' ]:
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                yield Token(kind=TokenType.BRACKET, value=c, row=self.row, col=self.col)
                token_row = self.row
                token_col = self.col + 1

            elif c == '#' and (not parsing or ptype == 2):
                parsing = True
                ptype   = 2

            elif c == '"' and (not parsing or ptype == 1):
                if not parsing:
                    parsing = True
                    ptype   = 1
                    token_row   = self.row
                    token_col   = self.col
                else:
                    parsing = False
                    ptype   = 0
                    yield Token(kind=TokenType.STRING, value=token, row=token_row, col=token_col)
                    token = ''
            else:
                token += c

            self.col += 1

    def second_pass(self):
        for token in self.first_pass():
            if token.kind != TokenType.UNKNOWN:
                pass

            elif token.value == 'null':
                token.kind = TokenType.NULL

            elif token.value in [ 'true', 'false' ]:
                token.kind = TokenType.BOOLEAN

            elif can_convert_to(int, token.value):
                token.kind = TokenType.INTEGER

            elif can_convert_to(float, token.value):
                token.kind = TokenType.FLOAT

            else: 
                token.kind = TokenType.IDENTIFIER

            yield token

