import struct

from enum   import Enum, auto
from tokenizer import TokenType
from parser import Node, ExprType, print_ast

def f32_to_hex(number):
    u32_repr = struct.unpack('@Q', struct.pack('@d', float(number)))[0]
    return '0x{:X}'.format(u32_repr & 0xFFFF_FFFF_E000_0000)

class Program:
    def __init__(self):
        self.type_count  = 0
        self.reg_count   = 0
        self.label_count = 0
        self.indent      = 0
        self.declared    = {}
        self.code        = ''
        self.globals     = ''
        self.scope       = { 'main': {} }
        self.current_scope = 'main'


    def new_register(self):
        register = '%r' + str(self.reg_count)
        self.reg_count += 1
        return register


    def last_register(self):
        return '%r' + str(self.reg_count - 1)


    def new_type(self):
        type_name = '%t' + str(self.type_count)
        self.type_count += 1
        return type_name


    def new_label(self):
        label_name = 'lbl' + str(self.label_count)
        self.label_count += 1
        return label_name


    def instr(self, instruction, *args):
        if len(args) > 0:
            return ' ' * self.indent + instruction.format(*args) + '\n'
        else:
            return ' ' * self.indent + instruction + '\n'


    def comment(self, comment):
        self.code += '; {}\n'.format(comment)


    def empty_line(self):
        self.code += '\n'

    
    def change_scope(self, scope):
        self.current_scope = scope


    def declare_variable(self, var_type, var_name):
        var_ptr = self.alloca(var_type)
        self.scope[self.current_scope][var_name] = (var_type, var_ptr)


    def get_variable_type(self, var_name):
        return self.scope[self.current_scope][var_name][0]


    def get_variable_ptr(self, var_name):
        return self.scope[self.current_scope][var_name][1]


    def type(self, declaration):
        try:
            type_reg = self.declared[hash(declaration)]
        except:
            type_reg      = self.new_type()
            self.globals += '{} = type {}\n'.format(type_reg, declaration)
            self.declared[hash(declaration)] = type_reg
        return type_reg


    def label(self, name):
        self.code += name + ':\n'


    def load(self, store_type, value_type, value):
        reg = self.new_register()
        self.code += self.instr('{} = load {}, {} {}', reg, store_type, value_type, value)
        return reg


    def store(self, value_type, value, store_type, store_reg):
        self.code += self.instr('store {} {}, {} {}', value_type, value, store_type, store_reg)


    def alloca(self, mem_type):
        ptr = self.new_register()
        self.code += self.instr('{} = alloca {}', ptr, mem_type)
        return ptr


    def get_element_ptr(self, mem_type, reg_type, reg_name, *args):
        ptr   = self.new_register()
        instr = '{} = getelementptr {}, {} {}'.format(ptr, mem_type, reg_type, reg_name)

        it = iter(args)
        for arg_type, arg_value in zip(it, it):
            instr += ', {} {}'.format(arg_type, arg_value)

        self.code += self.instr(instr)
        return ptr


    def call(self, fn_type, fn_name, *args):
        args_lst = []

        it = iter(args)
        for arg_type, arg_value in zip(it, it):
            args_lst.append('{} {}'.format(arg_type, arg_value))

        reg        = self.new_register()
        self.code += self.instr('{} = call {} {}({})', reg, fn_type, fn_name, ', '.join(args_lst))
        return reg


    def br_if_else(self, cond_reg, true_lbl, false_lbl):
        self.code += self.instr('br i1 {}, label %{}, label %{}', cond_reg, true_lbl, false_lbl)


    def br(self, label):
        self.code += self.instr('br label %{}', label)


    def fpext(self, fp_reg):
        dbl_reg = self.new_register()
        self.code += self.instr('{} = fpext float {} to double', dbl_reg, fp_reg)
        return dbl_reg


    def add(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = add {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def fadd(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = fadd {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def sub(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = sub {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def fsub(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = fsub {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def mul(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = mul {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def fmul(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = fmul {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def sdiv(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = sdiv {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def fdiv(self, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = fdiv {} {}, {}', reg, reg_type, a_reg, b_reg)
        return reg


    def icmp(self, cmp_type, reg_type, a_reg, b_reg):
        reg = self.new_register()
        self.code += self.instr('{} = icmp {} {} {}, {}', reg, cmp_type, reg_type, a_reg, b_reg)
        return reg


class Generator:
    def __init__(self, vrs, ops):
        self.program = Program()
        self.vars  = vrs
        self.ops   = ops
        self.stack = [[]]
        self.global_types = set()

        self.builtin_ops = {
            'print'  : self.generate_print,
            'is'     : self.generate_declare,
            '='      : self.generate_assign,
            '+'      : self.generate_add,
            '-'      : self.generate_sub,
            '*'      : self.generate_mul,
            '/'      : self.generate_div,
            '=='     : self.generate_eq,
            '<'      : self.generate_lt,
            '@'      : self.generate_at,
            '?'      : self.generate_if,
            'repeat' : self.generate_repeat,
            'list'   : self.generate_list,
            'block'  : self.generate_block,
        }

    def generate(self, node):
        self.program.indent += 4
        self.generate_args()
        self.generate_block(node)

        code = ''

        for decl in self.program.globals:
            code += decl

        code += 'declare i32 @printf(i8*, ...)\n'
        code += 'declare i32 @puts(i8*)\n'
        code += 'define i32 @main(i32 %argc, i8** %argv)\n'
        code += '{\n'
        code +=      self.program.code
        code += '    ret i32 0\n'
        code += '}\n'
        return code


    def generate_args(self):
        self.program.comment('argc is i32')
        self.program.declare_variable('i32',  'argc')
        self.program.empty_line()

        self.program.comment('argc = %argc')
        self.program.store('i32',  '%argc', 'i32*',  self.program.get_variable_ptr('argc'))
        self.program.empty_line()

        self.program.comment('argv is [list, i8]')
        self.program.declare_variable('i8**', 'argv')
        self.program.empty_line()

        self.program.comment('argv = %argv')
        self.program.store('i8**', '%argv', 'i8***', self.program.get_variable_ptr('argv'))
        self.program.empty_line()


    def generate_node(self, node):
        if node.token.value in [ 'list', 'block' ] or len(node.children) > 0:
            return self.builtin_ops[node.token.value](node)

        if node.token.kind == TokenType.IDENTIFIER:
            try:
                var_type = self.program.get_variable_type(node.token.value)
                var_ptr  = self.program.get_variable_ptr(node.token.value)
                                    
                if var_type == 'i32':
                    node.expr_type = ExprType.I32
                elif var_type == 'float':
                    node.expr_type = ExprType.F32

                return node, var_ptr, var_type,

            except Exception as e: # Could be a declaration
                pass
            return node, None,

        if node.expr_type == ExprType.VOID:
            self.program.comment(node.to_code())
            self.program.empty_line()
            return node, None,

        if node.expr_type == ExprType.NULL:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('i64')
            self.program.store('i64', 0, 'i64*', ptr)
            self.program.empty_line()
            return node, ptr,

        if node.expr_type == ExprType.STRING:
            self.program.comment(node.to_code())
            ptr = self.generate_string(node.token.value)
            self.program.empty_line()
            return node, ptr,

        if node.expr_type == ExprType.BOOLEAN:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('i1')
            self.program.store('i1', node.token.value, 'i1*', ptr)
            self.program.empty_line()
            return node, ptr,

        if node.expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('i32')
            self.program.store('i32', node.token.value, 'i32*', ptr)
            self.program.empty_line()
            return node, ptr,

        if node.expr_type == ExprType.F32:
            self.program.comment(node.to_code())
            ptr = self.program.alloca('float')
            self.program.store('float', f32_to_hex(node.token.value), 'float*', ptr)
            self.program.empty_line()
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


    def generate_block(self, node):
        for child in node.children:
            self.generate_node(child)
        return node


    def generate_string(self, value):
        str_type = self.program.type('{{ i32, [{} x i8] }}'.format(len(value) + 1))
        ptr_type = str_type + '*'

        str_ptr = self.program.alloca(str_type)
        idx_ptr = self.program.get_element_ptr(str_type, ptr_type, str_ptr, 'i64', 0, 'i32', 1, 'i8', len(value))
        self.program.store('i8', 0, 'i8*', idx_ptr)

        for i in reversed(range(len(value))):
            idx_ptr = self.program.get_element_ptr(str_type, ptr_type, str_ptr, 'i64', 0, 'i32', 1, 'i8', i)
            self.program.store('i8', ord(value[i]), 'i8*', idx_ptr)

        str_ptr_ptr = self.program.alloca('i8*')
        self.program.store('i8*', idx_ptr, 'i8**', str_ptr_ptr)

        return str_ptr_ptr


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


    def generate_add(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I32:
            node.expr_type = ExprType.I32

            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.add('i32', lreg, rreg)
            vptr = self.program.alloca('i32')
            self.program.store('i32', vreg, 'i32*', vptr)
            self.program.empty_line()

        elif node.children[0].expr_type == ExprType.F32:
            node.expr_type = ExprType.F32

            self.program.comment(node.to_code())
            lreg = self.program.load('float', 'float*', lptr)
            rreg = self.program.load('float', 'float*', rptr)
            vreg = self.program.fadd('float', lreg, rreg)
            vptr = self.program.alloca('float')
            self.program.store('float', vreg, 'float*', vptr)
            self.program.empty_line()

        return node, vptr,


    def generate_sub(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.sub('i32', lreg, rreg)
            vptr = self.program.alloca('i32')
            self.program.store('i32', vreg, 'i32*', vptr)
            self.program.empty_line()

        elif node.children[0].expr_type == ExprType.F32:
            self.program.comment(node.to_code())
            lreg = self.program.load('float', 'float*', lptr)
            rreg = self.program.load('float', 'float*', rptr)
            vreg = self.program.fsub('float', lreg, rreg)
            vptr = self.program.alloca('float')
            self.program.store('float', vreg, 'float*', vptr)
            self.program.empty_line()

        return node, vptr,


    def generate_mul(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.mul('i32', lreg, rreg)
            vptr = self.program.alloca('i32')
            self.program.store('i32', vreg, 'i32*', vptr)
            self.program.empty_line()

        elif node.children[0].expr_type == ExprType.F32:
            self.program.comment(node.to_code())
            lreg = self.program.load('float', 'float*', lptr)
            rreg = self.program.load('float', 'float*', rptr)
            vreg = self.program.fmul('float', lreg, rreg)
            vptr = self.program.alloca('float')
            self.program.store('float', vreg, 'float*', vptr)
            self.program.empty_line()

        return node, vptr,


    def generate_div(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.sdiv('i32', lreg, rreg)
            vptr = self.program.alloca('i32')
            self.program.store('i32', vreg, 'i32*', vptr)
            self.program.empty_line()

        elif node.children[0].expr_type == ExprType.F32:
            self.program.comment(node.to_code())
            lreg = self.program.load('float', 'float*', lptr)
            rreg = self.program.load('float', 'float*', rptr)
            vreg = self.program.fdiv('float', lreg, rreg)
            vptr = self.program.alloca('float')
            self.program.store('float', vreg, 'float*', vptr)
            self.program.empty_line()

        return node, vptr,


    def generate_lt(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.icmp('slt', 'i32', lreg, rreg)
            vptr = self.program.alloca('i1')
            self.program.store('i1', vreg, 'i1*', vptr)
            self.program.empty_line()

        return node, vptr


    def generate_eq(self, node):
        if node.children[0].expr_type != node.children[1].expr_type:
            raise TypeError('Mismatched types')

        lnode, lptr, *_ = self.generate_node(node.children[0]);
        rnode, rptr, *_ = self.generate_node(node.children[1]);

        if node.children[0].expr_type == ExprType.I8:
            self.program.comment(node.to_code())
            lreg = self.program.load('i8', 'i8*', lptr)
            rreg = self.program.load('i8', 'i8*', rptr)
            vreg = self.program.icmp('eq', 'i8', lreg, rreg)
            vptr = self.program.alloca('i1')
            self.program.store('i1', vreg, 'i1*', vptr)
            self.program.empty_line()

        if node.children[0].expr_type == ExprType.I32:
            self.program.comment(node.to_code())
            lreg = self.program.load('i32', 'i32*', lptr)
            rreg = self.program.load('i32', 'i32*', rptr)
            vreg = self.program.icmp('eq', 'i32', lreg, rreg)
            vptr = self.program.alloca('i1')
            self.program.store('i1', vreg, 'i1*', vptr)
            self.program.empty_line()

        return node, vptr
    

    def generate_declare(self, node):
        lleaf, *_ = self.generate_node(node.children[0]);
        rleaf, *_ = self.generate_node(node.children[1]);

        llvm_type = rleaf.token.value
        
        if llvm_type == 'f32':
            llvm_type = 'float'
        elif llvm_type == 'f64':
            llvm_type = 'double'

        self.program.comment(node.to_code())
        self.program.declare_variable(llvm_type, lleaf.token.value)
        self.program.empty_line()
        return node, 


    def generate_assign(self, node):
        lleaf, lptr, *_ = self.generate_node(node.children[0])
        rleaf, rptr, *_ = self.generate_node(node.children[1])

        if lleaf.expr_type == ExprType.I32:
            ltype = 'i32'

        elif lleaf.expr_type == ExprType.F32:
            ltype = 'float'

        self.program.comment(node.to_code())
        ptr = self.program.load(ltype, ltype + '*', rptr)
        self.program.store(ltype, ptr, ltype + '*', lptr)
        self.program.empty_line()
        return node, 
    

    def generate_if(self, node):
        true_lbl  = self.program.new_label()
        false_lbl = self.program.new_label()
        end_lbl   = self.program.new_label()

        self.program.comment(node.to_code())
        lleaf, lptr, *_ = self.generate_node(node.children[0])
        lreg = self.program.load('i1', 'i1*', lptr)

        self.program.br_if_else(lreg, true_lbl, false_lbl)
        self.program.label(true_lbl)

        self.generate_node(node.children[1])

        self.program.br(end_lbl)
        self.program.label(false_lbl)
        self.program.br(end_lbl)
        self.program.label(end_lbl)

        vptr = self.program.alloca('i1')
        vreg = self.program.icmp('eq', 'i1', lreg, 0)
        self.program.store('i1', vreg, 'i1*', vptr)
        
        self.program.empty_line()
        return node, vptr,
    

    def generate_repeat(self, node):
        repeat_lbl  = self.program.new_label()
        inside_lbl  = self.program.new_label()
        outside_lbl = self.program.new_label()
        end_lbl     = self.program.new_label()

        self.program.comment(node.to_code())
        self.program.br(repeat_lbl)
        self.program.label(repeat_lbl)

        lleaf, lptr, *_ = self.generate_node(node.children[0])
        lreg = self.program.load('i1', 'i1*', lptr)

        self.program.br_if_else(lreg, inside_lbl, outside_lbl)
        self.program.label(inside_lbl)

        self.generate_node(node.children[1])

        self.program.br(repeat_lbl)
        self.program.label(outside_lbl)
        self.program.br(end_lbl)
        self.program.label(end_lbl)
        self.program.empty_line()
        return node, None,

    def generate_at(self, node):
        lleaf, lptr, *_ = self.generate_node(node.children[0])
        rleaf, rptr, *_ = self.generate_node(node.children[1])

        if lleaf.expr_type == ExprType.STRING or lleaf.sub_types[0] == ExprType.I8:
            lidxt = 'i8'
            lregt = 'i8*'
            lptrt = 'i8**'

        elif lleaf.sub_types[0] == ExprType.I32:
            lidxt = 'i32'
            lregt = 'i32*'
            lptrt = 'i32**'

        elif lleaf.sub_types[0] == ExprType.STRING:
            lidxt = 'i8*'
            lregt = 'i8**'
            lptrt = 'i8***'
        
        self.program.comment(node.to_code())
        lreg = self.program.load(lregt, lptrt,  lptr)
        rreg = self.program.load('i32', 'i32*', rptr)

        vreg = self.program.get_element_ptr(lidxt, lregt, lreg, 'i32', rreg)
        vidx = self.program.load(lidxt, lregt, vreg)

        vptr = self.program.alloca(lidxt)
        self.program.store(lidxt, vidx, lregt, vptr)
        self.program.empty_line()
        return node, vptr,

