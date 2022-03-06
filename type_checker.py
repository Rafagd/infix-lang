from tokenizer import TokenType
from parser    import Node, ExprType, print_ast

class TypeChecker:
    def __init__(self):
        self.var_defs = [{
            'argc' : 'i32',
            'argv' : 'list,string',
        }]

        self.ops_defs = {
            ';': [
                (ExprType.ANY, ExprType.ANY, ExprType.VOID),
            ],
            'is': [
                (ExprType.ANY, ExprType.ANY, ExprType.ANY),
            ],
            '=': [
                (ExprType.ANY, ExprType.ANY, ExprType.ANY),
            ],
            'print': [
                (ExprType.VOID, ExprType.ANY, ExprType.VOID),
            ],
            '?': [
                (ExprType.BOOLEAN, ExprType.BLOCK, ExprType.BOOLEAN),
            ],
            'repeat': [
                (ExprType.BOOLEAN, ExprType.BLOCK, ExprType.VOID),
            ],
            '+': [
                (ExprType.I32, ExprType.I32, ExprType.I32),
                (ExprType.F32, ExprType.F32, ExprType.F32),
            ],
            '-': [
                (ExprType.I32, ExprType.I32, ExprType.I32),
                (ExprType.F32, ExprType.F32, ExprType.F32),
            ],
            '*': [
                (ExprType.I32, ExprType.I32, ExprType.I32),
                (ExprType.F32, ExprType.F32, ExprType.F32),
            ],
            '/': [
                (ExprType.I32, ExprType.I32, ExprType.I32),
                (ExprType.F32, ExprType.F32, ExprType.F32),
            ],
            '<': [
                (ExprType.I32, ExprType.I32, ExprType.BOOLEAN),
                (ExprType.F32, ExprType.F32, ExprType.BOOLEAN),
            ],
            '==': [
                (ExprType.I8,  ExprType.I8,  ExprType.BOOLEAN),
                (ExprType.I32, ExprType.I32, ExprType.BOOLEAN),
                (ExprType.F32, ExprType.F32, ExprType.BOOLEAN),
                (ExprType.F64, ExprType.F64, ExprType.BOOLEAN),
            ],
            '@': [
                (ExprType.LIST,   ExprType.I32, ExprType.STRING),
                (ExprType.STRING, ExprType.I32, ExprType.I8),
            ],
        }

    def coerses_to(self, type_a, type_b):
        if type_a == type_b:
            return True

        if type_b == ExprType.ANY:
            return True

        if type_b == ExprType.F32:
            return type_a in [
                ExprType.I8,
                ExprType.I32,
            ]

        return False

    def check(self, node) -> Node:
        if len(node.children) == 0:
            return self.check_leaf(node)

        valid = True
        for child in node.children:
            if self.check(child).expr_type == ExprType.INVALID:
                valid = False

        if not valid:
            node.expr_type = ExprType.INVALID
            return node

        if node.expr_type == ExprType.LIST:
            node.sub_types.append(node.children[0].expr_type)
            return node

        if node.expr_type == ExprType.BLOCK:
            return node

        op_defs = self.ops_defs[node.token.value]
        if node.token.value == 'is':
            self.var_defs[-1][node.children[0].token.value] = node.children[1].token.value
        
        for op in op_defs:
            lhs_type = node.children[0].expr_type
            rhs_type = node.children[1].expr_type

            error = ''

            if not self.coerses_to(lhs_type, op[0]):
                error += 'Operation {} expects a {} as left operand, got {}\n'.format(
                    node.token.value, op[0], lhs_type)

            if not self.coerses_to(rhs_type, op[1]):
                error += 'Operation {} expects a {} as right operand, got {}\n'.format(
                    node.token.value, op[1], rhs_type)

            if node.token.value == ';':
                node.expr_type = rhs_type
                return node
            elif error == '':
                node.expr_type = op[2]
                return node
            
        print(error)
        node.expr_type = ExprType.VOID
        return node


    def check_leaf(self, leaf):
        if leaf.expr_type != ExprType.VOID:
            pass

        elif leaf.token.kind == TokenType.NULL:
            leaf.expr_type = ExprType.NULL

        elif leaf.token.kind == TokenType.BOOLEAN:
            leaf.expr_type = ExprType.BOOLEAN

        elif leaf.token.kind == TokenType.INTEGER:
            leaf.expr_type = ExprType.I32

        elif leaf.token.kind == TokenType.FLOAT:
            leaf.expr_type = ExprType.F32

        elif leaf.token.kind == TokenType.STRING:
            leaf.expr_type = ExprType.STRING

        elif leaf.token.value in self.var_defs[-1]:
            var_type = self.var_defs[-1][leaf.token.value]

            if var_type == 'i32':
                leaf.expr_type = ExprType.I32
            if var_type == 'list,string':
                leaf.expr_type = ExprType.LIST
                leaf.sub_types = [ ExprType.STRING ]
        else:
            leaf.expr_type = ExprType.VOID

        return leaf

