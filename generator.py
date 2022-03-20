import struct

from dataclasses import dataclass
from enum      import Enum, auto
from tokenizer import TokenType
from parser    import Node, ExprType, print_ast
from llvm      import Module, Type, Variable, ProgramUnknownOperationError

def f32_to_hex(number):
    u32_repr = struct.unpack('@Q', struct.pack('@d', float(number)))[0]
    return '0x{:X}'.format(u32_repr & 0xFFFF_FFFF_E000_0000)

@dataclass
class Result:
    name: str  = None
    type: Type = None
    
    def __post_init__(self):
        if self.name is None:
            self.type = Type(name='%void', repr='void', primitive=True)
        elif self.type is None:
            raise Exception('Result must have a type unless void')
            

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
            'is'     : self.generate_declare,
            '='      : self.generate_assign,
            '?'      : self.generate_if,
            'repeat' : self.generate_repeat,
            'return' : self.generate_return,
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

    def generate_return(self, node):
        ret = self.generate_node(node.children[1])
        self.module.ret(ret)
        return ret

    def generate_assign(self, node):
        pname = '%' + node.children[0].token.value
        reg   = self.generate_node(node.children[1])
        return self.module.assign(pname, reg)

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


    def generate_nodea(self, node):
        if node.token.value in [ 'list', 'block' ] or len(node.children) > 0:
            if node.token.value in self.builtin_ops:
                return self.builtin_ops[node.token.value](node)

            var_type = self.program.get_variable_type(node.token.value)
            if var_type == ExprType.BLOCK:
                return self.generate_op_call(node)

            raise Exception('Undeclared operation: ' + node.token.value)

        if node.token.kind == TokenType.IDENTIFIER:
            try:
                var_type = self.program.get_variable_type(node.token.value)
                var_ptr  = self.program.get_variable_ptr(node.token.value)
                                    
                if var_type == 'i32':
                    node.expr_type = ExprType.I32
                elif var_type == 'float':
                    node.expr_type = ExprType.F32
                elif var_type == 'i8**':
                    node.expr_type = ExprType.LIST
                    node.sub_types = [ ExprType.STRING ]
                else:
                    raise Exception('Unknown type: ' + var_type)

                return node, var_ptr, var_type,

            except IndexError as e: # Could be a declaration
                pass
            return node, None,

        if node.token.kind == TokenType.VOID:
            self.program.comment(node.to_code())
            self.program.empty_line()
            return node, None,

        if node.token.kind == TokenType.NULL:
            self.program.comment(node.to_code())
            ptr = self.program.const_null()
            self.program.empty_line()

            node.expr_type = ExprType.NULL
            return node, ptr,

        if node.token.kind == TokenType.BOOLEAN:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('i1')
            self.program.store('i1', node.token.value, 'i1*', ptr)
            self.program.empty_line()

            node.expr_type = ExprType.BOOLEAN
            return node, ptr,

        if node.token.kind == TokenType.INTEGER:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('i32')
            self.program.store('i32', node.token.value, 'i32*', ptr)
            self.program.empty_line()

            node.expr_type = ExprType.I32
            return node, ptr,

        if node.token.kind == TokenType.FLOAT:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('float')
            self.program.store('float', f32_to_hex(node.token.value), 'float*', ptr)
            self.program.empty_line()

            node.expr_type = ExprType.F32
            return node, ptr,

        if node.token.kind == TokenType.STRING:
            self.program.comment(node.to_code())
            ptr = self.generate_string(node.token.value)
            self.program.empty_line()

            node.expr_type = ExprType.STRING
            return node, ptr,

        raise Exception(str(node))


    def generate_list(self, node):
        if len(node.sub_types) == 0:
            idx_reg_type = 'i32'
        elif node.sub_types[0] == ExprType.I32:
            idx_reg_type = 'i32'
        elif node.sub_types[0] == ExprType.STRING:
            idx_reg_type = 'i8*'
        else:
            raise Exception('Unsupported list of type: {}'.format(node.sub_types[0].name))

        children = []
        for child in node.children:
            _, r, *_ = self.generate_node(child)
            children.append(r)

        idx_ptr_type = idx_reg_type + '*'
        lst_reg_type = self.program.type('{{ i32, [{} x {}] }}'.format(len(children), idx_reg_type))
        lst_ptr_type = lst_reg_type + '*'

        self.program.comment(node.to_code())
        lst_ptr = self.program.alloca(lst_reg_type)
        siz_ptr = self.program.get_element_ptr(lst_reg_type, lst_ptr_type, lst_ptr, 'i64', 0, 'i32', 0)
        self.program.store('i32', str(len(node.children)), 'i32*', siz_ptr)

        for i, child in enumerate(children):
            val_reg = self.program.load(idx_reg_type, idx_ptr_type, child)
            idx_ptr = self.program.get_element_ptr(lst_reg_type, lst_ptr_type, lst_ptr, 'i64', 0, 'i32', 1, idx_reg_type, i)
            self.program.store(idx_reg_type, val_reg, idx_ptr_type, idx_ptr)

        self.program.empty_line()
        return node, lst_ptr,


    def generate_print(self, node):
        _               = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[1].expr_type == ExprType.VOID:
            self.program.comment(node.to_code())
            ptr = self.generate_string('void')
            reg = self.program.load('i8*', 'i8**', ptr)
            self.program.call('i32', '@puts', 'i8*', reg)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.NULL:
            self.program.comment(node.to_code())
            ptr = self.generate_string('null')
            reg = self.program.load('i8*', 'i8**', ptr)
            self.program.call('i32', '@puts', 'i8*', reg)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.BOOLEAN:
            self.program.comment(node.to_code())
            true_lbl  = self.program.new_label()
            false_lbl = self.program.new_label()
            end_lbl   = self.program.new_label()

            bool_reg = self.program.load('i1', 'i1*', rptr)
            self.program.br_if_else(bool_reg, true_lbl, false_lbl)
            
            self.program.label(true_lbl)
            ptr = self.generate_string('true')
            reg = self.program.load('i8*', 'i8**', ptr)
            self.program.call('i32', '@puts', 'i8*', reg)
            self.program.br(end_lbl)

            self.program.label(false_lbl)
            ptr = self.generate_string('false')
            reg = self.program.load('i8*', 'i8**', ptr)
            self.program.call('i32', '@puts', 'i8*', reg)
            self.program.br(end_lbl)

            self.program.label(end_lbl)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            sptr = self.generate_string('%d\n')
            sreg = self.program.load('i8*', 'i8**', sptr)
            i32_reg = self.program.load('i32', 'i32*', rptr)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', sreg, 'i32', i32_reg)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.F32:
            self.program.comment(node.to_code())
            sptr = self.generate_string('%f\n')
            sreg = self.program.load('i8*', 'i8**', sptr)
            f32_reg = self.program.load('float', 'float*', rptr)
            f64_reg = self.program.fpext(f32_reg)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', sreg, 'double', f64_reg)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.STRING:
            self.program.comment(node.to_code())
            rreg = self.program.load('i8*', 'i8**', rptr)
            self.program.call('i32', '@puts', 'i8*', rreg)
            self.program.empty_line()

        elif node.children[1].expr_type == ExprType.LIST:
            self.program.comment(node.to_code())
            
            ipat = self.generate_string('%d')
            spat = self.generate_string('%s')
            ipat = self.program.load('i8*', 'i8**', ipat)
            spat = self.program.load('i8*', 'i8**', spat)


            stbr = self.generate_string('[')
            sep  = self.generate_string(', ')
            edbr = self.generate_string(']')
            stbr = self.program.load('i8*', 'i8**', stbr)
            sep  = self.program.load('i8*', 'i8**', sep)
            edbr = self.program.load('i8*', 'i8**', edbr)

            self.program.call('i32(i8*, ...)', '@printf', 'i8*', spat, 'i8*', stbr)
            
            idx_ptr = self.program.alloca('i32')
            self.program.store('i32', '0', 'i32*', idx_ptr)

            size_ptr = self.program.alloca('i32')
            self.program.store('i32', str(len(node.children[1].children)), 'i32*', size_ptr)

            top_lbl   = self.program.new_label()
            true_lbl  = self.program.new_label()
            false_lbl = self.program.new_label()
            end_lbl   = self.program.new_label()
            self.program.br(top_lbl)
            self.program.label(top_lbl)

            idx_reg  = self.program.load('i32', 'i32*', idx_ptr)
            size_reg = self.program.load('i32', 'i32*', size_ptr)
            cmp_reg  = self.program.icmp('slt', 'i32', idx_reg, size_reg)

            self.program.br_if_else(cmp_reg, true_lbl, false_lbl)
            self.program.label(true_lbl)

            zerot_lbl = self.program.new_label()
            zerof_lbl = self.program.new_label()
            zeroe_lbl = self.program.new_label()
            zero_reg  = self.program.icmp('eq', 'i32', idx_reg, '0')
            self.program.br_if_else(zero_reg, zerot_lbl, zerof_lbl)
            self.program.label(zerot_lbl)
            self.program.br(zeroe_lbl)
            self.program.label(zerof_lbl)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', spat, 'i8*', sep)
            self.program.br(zeroe_lbl)
            self.program.label(zeroe_lbl)

            lst_reg_type = self.program.type('{{ i32, [{} x {}] }}'.format(len(node.children[1].children), 'i32'))
            lst_ptr_type = lst_reg_type + '*'
            val_ptr = self.program.get_element_ptr(lst_reg_type, lst_ptr_type, rptr, 'i64', 0, 'i32', 1, 'i32', idx_reg)
            val_reg = self.program.load('i32', 'i32*', val_ptr)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', ipat, 'i32', val_reg)

            nxt_reg = self.program.add('i32', idx_reg, 1)
            self.program.store('i32', nxt_reg, 'i32*', idx_ptr)

            self.program.br(top_lbl)
            self.program.label(false_lbl)
            self.program.br(end_lbl)
            self.program.label(end_lbl)

            self.program.call('i32', '@puts', 'i8*', edbr)

        return node,

