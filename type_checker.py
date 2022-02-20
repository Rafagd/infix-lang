from tokenizer import TokenType
from parser    import Node, Leaf, ExprType

class TypeChecker:
    def __init__(self):
        self.var_defs = [
        ]

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
            'if': [
                (ExprType.BOOLEAN, ExprType.VOID, ExprType.BOOLEAN),
            ],
            'while': [
                (ExprType.BOOLEAN, ExprType.VOID, ExprType.VOID),
            ],
            'argc': [
                (ExprType.VOID, ExprType.VOID, ExprType.I32),
            ],
            'argv': [
                (ExprType.VOID, ExprType.I32, ExprType.STRING),
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
        if isinstance(node, Leaf):
            return self.check_leaf(node)

        op_defs = self.ops_defs[node.operation.value]
        
        for op in op_defs:
            lhs_type = self.check(node.left).expr_type
            rhs_type = self.check(node.right).expr_type

            error = ''

            if not self.coerses_to(lhs_type, op[0]):
                error += 'Operation {} expects a {} as left operand, got {}\n'.format(
                    node.operation.value, op[0], lhs_type)

            if not self.coerses_to(rhs_type, op[1]):
                error += 'Operation {} expects a {} as right operand, got {}\n'.format(
                    node.operation.value, op[1], rhs_type)

            if node.operation.value == ';':
                node.expr_type = rhs_type
                return node
            elif error == '':
                node.expr_type = op[2]
                return node
            
        print(error)
        node.expr_type = ExprType.VOID
        return node


    def check_leaf(self, leaf):
        if leaf.token.kind == TokenType.NULL:
            leaf.expr_type = ExprType.NULL

        elif leaf.token.kind == TokenType.BOOLEAN:
            leaf.expr_type = ExprType.BOOLEAN

        elif leaf.token.kind == TokenType.INTEGER:
            leaf.expr_type = ExprType.I32

        elif leaf.token.kind == TokenType.FLOAT:
            leaf.expr_type = ExprType.F32

        elif leaf.token.kind == TokenType.STRING:
            leaf.expr_type = ExprType.STRING

        else:
            leaf.expr_type = ExprType.VOID

        return leaf

