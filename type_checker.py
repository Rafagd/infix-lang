from tokenizer import TokenType
from parser    import Node, Leaf, ExprType

class TypeChecker:
    def __init__(self):
        self.var_defs = [
        ]

        self.ops_defs = {
            ';':     (ExprType.VOID,    ExprType.VOID,   ExprType.VOID),
            'print': (ExprType.VOID,    ExprType.STRING, ExprType.VOID),
            'if':    (ExprType.BOOLEAN, ExprType.VOID,   ExprType.BOOLEAN),
            '+':     (ExprType.F32,     ExprType.F32,    ExprType.F32),
            '-':     (ExprType.F32,     ExprType.F32,    ExprType.F32),
            '*':     (ExprType.F32,     ExprType.F32,    ExprType.F32),
            '/':     (ExprType.F32,     ExprType.F32,    ExprType.F32),
        }

    def coerses_to(self, type_a, type_b):
        if type_a == type_b:
            return True

        if type_b in [ ExprType.VOID, ExprType.STRING ]:
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

        op_def = self.ops_defs[node.operation.value]
        
        lhs_type = self.check(node.left).expr_type
        rhs_type = self.check(node.right).expr_type

        if node.operation.value == ';':
            node.expr_type = rhs_type
        else:
            node.expr_type = op_def[2]

        if not self.coerses_to(lhs_type, op_def[0]):
            print('Operation {} expects a {} as left operand, got {}'.format(
                node.operation.value,
                op_def[0],
                lhs_type
            ))

        if not self.coerses_to(rhs_type, op_def[1]):
            print('Operation {} expects a {} as right operand, got {}'.format(
                node.operation.value,
                op_def[1],
                rhs_type
            ))

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

