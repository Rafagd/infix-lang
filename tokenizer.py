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
        parsing_str = False
        token       = ''
        token_row   = 1
        token_col   = 1

        for c in self.source:
            if c == '\n':
                self.row += 1
                self.col  = 0

            if not parsing_str and c.isspace():
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                token_row = self.row
                token_col = self.col + 1
            
            elif c == ';':
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                yield Token(kind=TokenType.IDENTIFIER, value=';', row=self.row, col=self.col)
                token_row = self.row
                token_col = self.col + 1

            elif c in [ '{', '(', '[', ']', ')', '}' ]:
                if token != '':
                    yield Token(kind=TokenType.UNKNOWN, value=token, row=token_row, col=token_col)
                    token = ''
                yield Token(kind=TokenType.BRACKET, value=c, row=self.row, col=self.col)
                token_row = self.row
                token_col = self.col + 1

            elif c == '"':
                if not parsing_str:
                    parsing_str = True
                    token_row   = self.row
                    token_col   = self.col
                else:
                    parsing_str = False
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

