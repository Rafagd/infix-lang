import struct

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


    def new_register(self):
        register = '%r' + str(self.reg_count)
        self.reg_count += 1
        return register


    def last_register(self):
        return '%r' + str(self.reg_count - 1)


    def new_type(self):
        type_name = '%t' + str(self.reg_count)
        self.type_count += 1
        return type_name


    def new_label(self):
        label_name = 'l' + str(self.label_count)
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


class Generator:
    def __init__(self, vrs, ops):
        self.program = Program()
        self.vars  = vrs
        self.ops   = ops
        self.stack = [[]]
        self.global_types = set()

        self.builtin_ops = {
            'print': self.generate_print,
            ';'    : self.generate_semicolon,
            '+'    : self.generate_add,
            '-'    : self.generate_sub,
            '*'    : self.generate_mul,
            '/'    : self.generate_div,
            'argc' : self.generate_argc,
            'argv' : self.generate_argv,
        }

    def generate(self, node):
        self.program.indent += 4
        self.generate_node(node)

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

    def generate_node(self, node):
        if isinstance(node, Node):
            try:
                return self.builtin_ops[node.operation.value](node)
            except:
                raise

        if node.expr_type == ExprType.VOID:
            return None

        if node.expr_type == ExprType.NULL:
            self.program.comment('null')
            ptr = self.program.alloca('i64')
            self.program.store('i64', 0, 'i64*', ptr)
            self.program.empty_line()
            return ptr

        if node.expr_type == ExprType.STRING:
            self.program.comment('string "{}"'.format(node.token.value))
            ptr = self.generate_string(node.token.value)
            self.program.empty_line()
            return ptr

        if node.expr_type == ExprType.BOOLEAN:
            self.program.comment('bool "{}"'.format(node.token.value))
            ptr = self.program.alloca('i1')
            self.program.store('i1', node.token.value, 'i1*', ptr)
            self.program.empty_line()
            return ptr

        if node.expr_type == ExprType.I32:
            self.program.comment('i32 "{}"'.format(node.token.value))
            ptr = self.program.alloca('i32')
            self.program.store('i32', node.token.value, 'i32*', ptr)
            self.program.empty_line()
            return ptr

        if node.expr_type == ExprType.F32:
            self.program.comment('f32 "{}"'.format(node.token.value))
            ptr = self.program.alloca('float')
            self.program.store('float', f32_to_hex(node.token.value), 'float*', ptr)
            self.program.empty_line()
            return ptr

#        raise Exception(str(node))


    def generate_string(self, value):
        str_type = self.program.type('{{ i32, [{} x i8] }}'.format(len(value) + 1))
        ptr_type = str_type + '*'

        str_ptr = self.program.alloca(str_type)
        idx_ptr = self.program.get_element_ptr(str_type, ptr_type, str_ptr, 'i64', 0, 'i32', 1, 'i8', len(value))
        self.program.store('i8', 0, 'i8*', idx_ptr)

        for i in reversed(range(len(value))):
            idx_ptr = self.program.get_element_ptr(str_type, ptr_type, str_ptr, 'i64', 0, 'i32', 1, 'i8', i)
            self.program.store('i8', ord(value[i]), 'i8*', idx_ptr)

        return idx_ptr


    def generate_print(self, node):
        _         = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);

        if node.right.expr_type == ExprType.VOID:
            self.program.comment('print(void)')
            ptr = self.generate_string('void')
            self.program.call('i32', '@puts', 'i8*', ptr)
            self.program.empty_line()

        elif node.right.expr_type == ExprType.NULL:
            self.program.comment('print(null)')
            ptr = self.generate_string('null')
            self.program.call('i32', '@puts', 'i8*', ptr)
            self.program.empty_line()

        elif node.right.expr_type == ExprType.BOOLEAN:
            self.program.comment('print(bool)')
            true_lbl  = self.program.new_label()
            false_lbl = self.program.new_label()
            end_lbl   = self.program.new_label()

            bool_reg = self.program.load('i1', 'i1*', right_ptr)
            self.program.br_if_else(bool_reg, true_lbl, false_lbl)
            
            self.program.label(true_lbl)
            ptr = self.generate_string('true')
            self.program.call('i32', '@puts', 'i8*', ptr)
            self.program.br(end_lbl)

            self.program.label(false_lbl)
            ptr = self.generate_string('false')
            self.program.call('i32', '@puts', 'i8*', ptr)
            self.program.br(end_lbl)

            self.program.label(end_lbl)
            self.program.empty_line()

        elif node.right.expr_type == ExprType.I32:
            self.program.comment('print(i32)')
            str_ptr = self.generate_string('%d\n')
            i32_reg = self.program.load('i32', 'i32*', right_ptr)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', str_ptr, 'i32', i32_reg)
            self.program.empty_line()

        elif node.right.expr_type == ExprType.F32:
            self.program.comment('print(f32)')
            str_ptr = self.generate_string('%f\n')
            f32_reg = self.program.load('float', 'float*', right_ptr)
            f64_reg = self.program.fpext(f32_reg)
            self.program.call('i32(i8*, ...)', '@printf', 'i8*', str_ptr, 'double', f64_reg)
            self.program.empty_line()

        elif node.right.expr_type == ExprType.STRING:
            self.program.comment('print(string)')
            self.program.call('i32', '@puts', 'i8*', right_ptr)
            self.program.empty_line()

        return None


    def generate_semicolon(self, node):
        self.generate_node(node.left);
        self.generate_node(node.right);


    def generate_add(self, node):
        if node.left.expr_type != node.right.expr_type:
            raise TypeError('Mismatched types')

        left_ptr  = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);

        if node.left.expr_type == ExprType.I32:
            self.program.comment('i32 + i32')
            left_reg  = self.program.load('i32', 'i32*', left_ptr)
            right_reg = self.program.load('i32', 'i32*', right_ptr)
            res_reg   = self.program.add('i32', left_reg, right_reg)
            res_ptr   = self.program.alloca('i32')
            self.program.store('i32', res_reg, 'i32*', res_ptr)
            self.program.empty_line()

        elif node.left.expr_type == ExprType.F32:
            self.program.comment('f32 + f32')
            left_reg  = self.program.load('float', 'float*', left_ptr)
            right_reg = self.program.load('float', 'float*', right_ptr)
            res_reg   = self.program.fadd('float', left_reg, right_reg)
            res_ptr   = self.program.alloca('float')
            self.program.store('float', res_reg, 'float*', res_ptr)
            self.program.empty_line()

        return res_ptr


    def generate_sub(self, node):
        if node.left.expr_type != node.right.expr_type:
            raise TypeError('Mismatched types')

        left_ptr  = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);

        if node.left.expr_type == ExprType.I32:
            self.program.comment('i32 - i32')
            left_reg  = self.program.load('i32', 'i32*', left_ptr)
            right_reg = self.program.load('i32', 'i32*', right_ptr)
            res_reg   = self.program.sub('i32', left_reg, right_reg)
            res_ptr   = self.program.alloca('i32')
            self.program.store('i32', res_reg, 'i32*', res_ptr)
            self.program.empty_line()

        elif node.left.expr_type == ExprType.F32:
            self.program.comment('f32 - f32')
            left_reg  = self.program.load('float', 'float*', left_ptr)
            right_reg = self.program.load('float', 'float*', right_ptr)
            res_reg   = self.program.fsub('float', left_reg, right_reg)
            res_ptr   = self.program.alloca('float')
            self.program.store('float', res_reg, 'float*', res_ptr)
            self.program.empty_line()

        return res_ptr


    def generate_mul(self, node):
        if node.left.expr_type != node.right.expr_type:
            raise TypeError('Mismatched types')

        left_ptr  = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);

        if node.left.expr_type == ExprType.I32:
            self.program.comment('i32 - i32')
            left_reg  = self.program.load('i32', 'i32*', left_ptr)
            right_reg = self.program.load('i32', 'i32*', right_ptr)
            res_reg   = self.program.mul('i32', left_reg, right_reg)
            res_ptr   = self.program.alloca('i32')
            self.program.store('i32', res_reg, 'i32*', res_ptr)
            self.program.empty_line()

        elif node.left.expr_type == ExprType.F32:
            self.program.comment('f32 - f32')
            left_reg  = self.program.load('float', 'float*', left_ptr)
            right_reg = self.program.load('float', 'float*', right_ptr)
            res_reg   = self.program.fmul('float', left_reg, right_reg)
            res_ptr   = self.program.alloca('float')
            self.program.store('float', res_reg, 'float*', res_ptr)
            self.program.empty_line()

        return res_ptr


    def generate_div(self, node):
        if node.left.expr_type != node.right.expr_type:
            raise TypeError('Mismatched types')

        left_ptr  = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);

        if node.left.expr_type == ExprType.I32:
            self.program.comment('i32 - i32')
            left_reg  = self.program.load('i32', 'i32*', left_ptr)
            right_reg = self.program.load('i32', 'i32*', right_ptr)
            res_reg   = self.program.sdiv('i32', left_reg, right_reg)
            res_ptr   = self.program.alloca('i32')
            self.program.store('i32', res_reg, 'i32*', res_ptr)
            self.program.empty_line()

        elif node.left.expr_type == ExprType.F32:
            self.program.comment('f32 - f32')
            left_reg  = self.program.load('float', 'float*', left_ptr)
            right_reg = self.program.load('float', 'float*', right_ptr)
            res_reg   = self.program.fdiv('float', left_reg, right_reg)
            res_ptr   = self.program.alloca('float')
            self.program.store('float', res_reg, 'float*', res_ptr)
            self.program.empty_line()

        return res_ptr


    def generate_argc(self, node):
        self.generate_node(node.left);
        self.generate_node(node.right);
        res_ptr = self.program.alloca('i32')
        self.program.store('i32', '%argc', 'i32*', res_ptr)
        return res_ptr

    def generate_argv(self, node):
        _         = self.generate_node(node.left);
        right_ptr = self.generate_node(node.right);
        right_reg = self.program.load('i32', 'i32*', right_ptr)
        argv_ptr  = self.program.get_element_ptr('i8*', 'i8**', '%argv', 'i32', right_reg)
        argv_reg  = self.program.load('i8*', 'i8**', argv_ptr)
        return argv_reg

