from __future__  import annotations

import pprint

from dataclasses import dataclass
from enum        import Enum, auto
from copy        import copy

from src.tokenizer   import TokenType, Token

class ExprType(Enum):
    INVALID = auto()
    ANY     = auto()
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
    LIST    = auto()
    BLOCK   = auto()


@dataclass
class Node:
    expr_type: ExprType       = ExprType.VOID
    sub_types: List[ExprType] = None
    token:     Token          = None
    children:  List[Node]     = None
    start:     int            = 0
    end:       int            = 0

    def __post_init__(self):
        if self.sub_types is None:
            self.sub_types = []

        if not isinstance(self.token, Token):
            raise Exception('Not a token')

        if self.token is None:
            self.token = Token()

        if self.children is None:
            self.children = []

    def to_code(self, brackets=False):
        if self.token.value == 'list':
            code = ''
            for child in self.children:
                code += child.to_code(brackets=True) + ', '
            if brackets:
                return '(' + code[:-1] + ')'
            return code[:-1]

        if self.token.value == 'block':
            children = ''
            for child in self.children:
                children += child.to_code() + '; '
            return '{' + children[:-1] + '}'

        if len(self.children) > 0:
            code = '{} {} {}'.format(
                self.children[0].to_code(brackets=True),
                self.token.value,
                self.children[1].to_code(),
            )
            if brackets:
                return '(' + code + ')'
            return code

        if self.token.kind == TokenType.STRING:
            return '"' + self.token.value + '"'
        return self.token.value

    def __str__(self):
        return repr(self)

    def __repr__(self):
        children = ', '.join([ repr(child) for child in self.children ])
        return '{{{} {} [{}]}}'.format(self.expr_type.name, self.token.value, children)


class Parser:
    def __init__(self, tokens):
        self.tokens = [ token for token in tokens ]
        self.ident  = 0

    def parse(self):
        ast, _ = self.first_pass()
        return ast

    def build_node(self, expr, sep):
        if sep == ',':
            children = []
            for term in expr:
                if isinstance(term, Node):
                    children.append(term)
                elif term.value != ',':
                    children.append(Node(token=term))
            node = Node(
                token     = Token(kind=TokenType.IDENTIFIER, value='list'),
                expr_type = ExprType.LIST,
                children  = children
            )
        else:
            while len(expr) > 1:
                if len(expr) < 3:
                    raise Exception('Insufficient expression terms')

                right = expr.pop()
                op    = expr.pop()
                left  = expr.pop()

                if isinstance(right, Token):
                    right = Node(token=right)

                if isinstance(left, Token):
                    left = Node(token=left)

                if not isinstance(op, Token):
                    raise Exception('Only identifiers are allowed as operations. Missing ;?')

                expr.append(Node(token=op, children=[ left, right ]))

            if len(expr) != 0:
                node = expr[0]
            else:
                node = Node(token=Token(value='void', kind=TokenType.VOID))

        return node


    def first_pass(self, index=0, open_bracket=''):
        global OPEN_BRACES
        global CLOSE_BRACES
        
        lst  = []
        expr = []
        sep  = None
        while index < len(self.tokens):
            token = self.tokens[index]

            if token.value in OPEN_BRACES:
                self.ident += 2
                r, index = self.first_pass(index + 1, token.value)
                expr.append(r)
                self.ident -= 2

            elif token.value in CLOSE_BRACES:

                if CLOSE_BRACES[token.value] != open_bracket:
                    raise Exception('Mismatched braces')

                if sep == None:
                    if len(expr) == 0: # ()
                        prev = self.tokens[index-1]
                        node = Node(
                            token = Token(
                                kind  = TokenType.VOID,
                                value = 'void',
                                row   = prev.row,
                                col   = prev.col,
                            ),
                            expr_type = ExprType.VOID,
                        )
                        return node, index

                    elif len(expr) == 1:
                        if isinstance(expr[0], Node):
                            node = expr[0]
                        else:
                            node = Node(token=expr[0])
                        return node, index

                    else:
                        return self.build_node(expr, ';'), index

                elif sep == ',':
                    node = self.build_node(expr, sep)
                    return node, index
                
                elif len(expr) == 1:
                    if isinstance(expr[0], Token):
                        node = Node(token=expr[0])
                    else:
                        node = expr[0]
                    return node, index

                else:
                    break;

            elif token.value == ',' and sep in [ None, ',' ]:
                sep  = ','

            elif token.value == ';' and sep in [ None, ';' ]:
                sep  = ';'
                lst.append(self.build_node(expr, sep))
                expr = []

            elif token.value in [ ',', ';' ]:
                raise Exception('Only one separator operator per expression')

            else:
                expr.append(token)

            index += 1

        if len(expr) > 0:
            lst.append(self.build_node(expr, ';'))

        return Node(
            token     = Token(kind=TokenType.IDENTIFIER, value='block'),
            expr_type = ExprType.BLOCK,
            children  = lst if sep != ',' else expr,
        ), index

    def second_pass(self, fp, index=0):
        return fp, index


def print_ast(node, depth=0):
    name = str(node.token.value if node.token is not None else 'void')
    if name == '':
        name = '∅'

    kind = [ node.expr_type ]
    kind.extend(node.sub_types)
    kind = ', '.join([ expr_type.name for expr_type in kind ])

    print(' ' * depth + name + ' (' + kind + ')')
    for child in node.children:
        print_ast(child, depth + 2)


OPEN_BRACES = {
    '{' : '}', 
    '(' : ')', 
    '[' : ']', 
}

CLOSE_BRACES = {
 '}' : '{', 
 ')' : '(', 
 ']' : '[', 
}
