from __future__ import annotations

from dataclasses import dataclass
from enum        import Enum, auto

from tokenizer import TokenType

class ExprType(Enum):
    VOID    = auto()
    NULL    = auto()
    BOOLEAN = auto()
    U8      = auto()
    U16     = auto()
    U32     = auto()
    U64     = auto()
    I8      = auto()
    I16     = auto()
    I32     = auto()
    I64     = auto()
    F32     = auto()
    F64     = auto()
    POINTER = auto()
    ARRAY   = auto()
    STRING  = auto()

@dataclass
class Leaf:
    token:     Token    = None
    expr_type: ExprType = ExprType.VOID
    start:     int      = 0
    end:       int      = 0

@dataclass
class Node:
    operation: Token    = None
    expr_type: ExprType = ExprType.VOID
    left:      Node     = None
    right:     Node     = None
    start:     int      = 0
    end:       int      = 0

class Parser:
    def __init__(self, tokens):
        self.tokens = [ t for t in tokens ]

    def parse(self, index=0, depth=0, bracket=''):
        node = Node(start=index, end=index)
        while index < len(self.tokens):
            nxt = None
            if self.tokens[index].kind == TokenType.BRACKET:
                value = self.tokens[index].value
                if value in [ '{', '(', '[' ]:
                    nxt   = self.parse(index + 1, depth + 1, value)
                    index = nxt.end + 1
                elif \
                    (bracket == '{' and value == '}') or \
                    (bracket == '(' and value == ')') or \
                    (bracket == '[' and value == ']'):
                    bracket = ''
                    break
                else:
                    raise Exception('Mismatching brackets: ', bracket, value, self.tokens[index])
            else:
                nxt = Leaf(token=self.tokens[index], start=index, end=index)

            if isinstance(nxt, Leaf) and nxt.token.value == ';':
                node.operation = nxt.token
            elif node.left is None:
                node.left = nxt
            elif node.operation is None:
                node.operation = nxt.token
            elif node.right is None:
                node.right = nxt
                node.end   = index
                node = Node(left=node, start=index + 1, end=index + 1)
            else:
                print('Parsing error: ', nxt)
                break;

            index += 1

        if bracket != '':
            raise Exception('Mismatching brackets')
        return node.left
 
def print_ast(node, depth=0):
    if isinstance(node, Node):
        print(' ' * depth + str(node.operation))
        print_ast(node.left,  depth + 2)
        print_ast(node.right, depth + 2)
    else:
        print(' ' * depth + str(node.token))
