import struct

from dataclasses import dataclass
from enum        import Enum, auto

from src.tokenizer import TokenType
from src.parser    import Node, ExprType, print_ast
from src.llvm      import Module, Type, Variable, ProgramUnknownOperationError

class Generator:
    def __init__(self):
        self.module = Module()

    def generate(self, node):
        self.generate_node(node)
        return self.module.to_llvm_ir()

    def generate_node(self, node):
        if node.expr_type == ExprType.BLOCK:
            return self.generate_block(node)

        if node.expr_type == ExprType.LIST:
            return self.generate_list(node)

        if node.token.kind != TokenType.IDENTIFIER:
            return self.generate_leaf(node)

        special_cases = {
            'as'     : self.generate_as,
            'is'     : self.generate_declare,
            '='      : self.generate_assign,
            '?'      : self.generate_if,
            'repeat' : self.generate_repeat,
            'return' : self.generate_return,
            'extern' : self.generate_extern,
            'called' : self.generate_called,
            'ptr-to' : self.generate_ptr_to,
        }
        
        if node.token.value in special_cases:
            return special_cases[node.token.value](node)

        if len(node.children) == 0:
            return self.module.variable('%' + node.token.value)

        results = []
        for child in node.children:
            results.append(self.generate_node(child))

        try:
            return self.module.call(node.token.value, results[0], results[1])
        except ProgramUnknownOperationError:
            raise
            
        # Normally, unreacheable
        return self.generate_unimpl(node)

    def generate_unimpl(self, node):
        for child in node.children:
            ret = self.generate_node(child)
        self.module.current.llvm.comment('Unimplemented node: ' + node.token.value)
        return Variable(type=self.module.type('%void'))

    def generate_block(self, node):
        for child in node.children:
            ret = self.generate_node(child)
        return ret

    def generate_declare(self, node):
        if node.children[1].token.kind != TokenType.IDENTIFIER:
            return self.generate_op_declare(node)

        if len(node.children[1].children) > 0:
            return self.generate_op_declare(node)

        rname = '%' + node.children[0].token.value
        rtype = self.module.type('%' + node.children[1].token.value)
        return self.module.new_variable(rname, rtype)

    def generate_op_declare(self, node):
        with self.module.function('@' + node.children[0].token.value):
            ret = self.generate_node(node.children[1])
            self.module.ret(ret)
            fn = self.module.current
        return fn.name

    def generate_extern(self, node):
        name  = '@' + node.children[0].token.value
        rtype = '%' + node.children[1].children[0].token.value
        args  = [ '%' + child.token.value for child in node.children[1].children[1:] ]
        self.module.add_external(name, rtype, args)
        return name

    def generate_called(self, node):
        args = []
        for child in node.children[1].children:
            args.append(self.generate_node(child))

        name = '@' + node.children[0].token.value
        return self.module.call_external(name, args)

    def generate_as(self, node):
        name = '%' + node.children[0].token.value
        type = '%' + node.children[1].token.value
        return self.module.cast(name, type)

    def generate_return(self, node):
        ret = self.generate_node(node.children[1])
        self.module.ret(ret)
        return ret

    def generate_assign(self, node):
        pname = '%' + node.children[0].token.value
        reg   = self.generate_node(node.children[1])
        return self.module.assign(pname, reg)

    def generate_ptr_to(self, node):
        pname = '%' + node.children[1].token.value
        return self.module.ptr_to(pname)

    def generate_if(self, node):
        cond = self.generate_node(node.children[0])
        with self.module.if_then(cond):
            self.generate_node(node.children[1])
        return self.module.negate(cond)

    def generate_repeat(self, node):
        with self.module.loop() as loop:
            cond  = self.generate_node(node.children[0])
            ncond = self.module.negate(cond)
            with self.module.if_then(ncond):
                loop.end()
            self.generate_node(node.children[1])

    def generate_list(self, node):
        children = []
        for child in node.children:
            reg = self.generate_node(child)
            children.append(reg)
        
        c0_type = None
        if len(children) > 0:
            c0_type = children[0].type

        if all(c0_type == child.type for child in children):
            reg = self.module.new_list(children)
        else:
            reg = self.module.new_struct(children)

        return reg

    def generate_leaf(self, leaf):
        llvm = self.module.current.llvm

        if leaf.token.kind == TokenType.VOID:
            leaf.expr_type = ExprType.VOID
            return Variable(type=self.module.type('%void'))

        if leaf.token.kind == TokenType.NULL:
            leaf.expr_type = ExprType.NULL
            return self.module.const_ptr('null')

        if leaf.token.kind == TokenType.BOOLEAN:
            leaf.expr_type = ExprType.BOOLEAN
            return self.module.const_bool(leaf.token.value)

        if leaf.token.kind == TokenType.INTEGER:
            leaf.expr_type = ExprType.I32
            return self.module.const_i32(leaf.token.value)

        if leaf.token.kind == TokenType.FLOAT:
            leaf.expr_type = ExprType.F32
            return self.module.const_f32(leaf.token.value)

        if leaf.token.kind == TokenType.STRING:
            leaf.expr_type = ExprType.STRING
            return self.module.const_cstr(leaf.token.value)

        raise Exception('Unknown type: ' + leaf.token.kind.name)


