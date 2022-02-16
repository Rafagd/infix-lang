import struct

from parser import Node, ExprType, print_ast

def get_element_ptr(var_type, var_name, *indexes):
    code  = 'getelementptr inbounds ' + var_type + ', '
    code += var_type + '* ' + var_name + ', '
    code += 'i64 0, i32 1'
    i = 0
    while i < len(indexes):
        code += ', ' + str(indexes[i]) + ' ' + str(indexes[i + 1])
        i += 2
    return code

def f32_to_hex(number):
    u32_repr  = struct.unpack('@Q', struct.pack('@d', number))[0]
    return u32_repr & 0xFFFF_FFFF_E000_0000
    u64_repr  = (0x8000_0000 & u32_repr) << 32 # Signal
    u64_repr |= (0x7E80_0000 & u32_repr) << 32 # Exponent
    u64_repr |= (0x007E_FFFF & u32_repr) << 29 # Exponent
    return u64_repr

class Generator:
    def __init__(self, vrs, ops):
        self.vars  = vrs
        self.ops   = ops
        self.stack = [[]]
        self.global_types = set()

        self.builtin_ops = {
            'print': self.generate_print,
            ';'    : self.generate_semicolon,
        }

    def generate(self, node):
        op_code = self.generate_node(node)

        code = ''

        for gtype in self.global_types:
            code += '%type.{:X} = {}\n'.format(hash(gtype), gtype).replace('-', 'Z')

        code += 'declare i32 @printf(i8*, ...)\n'
        code += 'declare i32 @puts(i8*)\n'
        code += 'define i32 @main()\n'
        code += '{\n'
        code +=      op_code
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
            return ''

        if node.expr_type == ExprType.NULL:
            var_name = self.new_stacked()
            code  = '{} = alloca i64\n'.format(var_name)
            code += 'store i64 0, i64* {}\n'.format(var_name)
            return code

        if node.expr_type == ExprType.STRING:
            return self.generate_string(node.token.value)

        if node.expr_type == ExprType.BOOLEAN:
            var_name = self.new_stacked()
            code  = '{} = alloca i1\n'.format(var_name)
            code += 'store i1 {}, i1* {}\n'.format(node.token.value, var_name)
            return code

        if node.expr_type == ExprType.I32:
            var_name = self.new_stacked()
            code  = '{} = alloca i32\n'.format(var_name)
            code += 'store i32 {}, i32* {}\n'.format(node.token.value, var_name)
            return code

        if node.expr_type == ExprType.F32:
            var_name = self.new_stacked()
            code  = '{} = alloca float\n'.format(var_name)
            code += 'store float 0x{:<016X}, float* {}\n'.format(f32_to_hex(float(node.token.value)), var_name)
            return code

        print(node)
        return 'Unknown!\n' # Leaf code

    def generate_string(self, value):
        var_name = self.new_stacked()
        var_type = self.new_type('type { i32, [' + str(len(value) + 1) + ' x i8] }')

        code = var_name + ' = alloca ' + var_type + '\n'
        for i, c in enumerate(value):
            code += var_name + '.index.' + str(i) + ' = ' + get_element_ptr(var_type, var_name, 'i8', i) + '\n'
            code += 'store i8 ' + str(ord(c)) + ', i8* ' + var_name + '.index.' + str(i) + '\n'
        code += var_name + '.last = ' + get_element_ptr(var_type, var_name, 'i8', i + 1) + '\n'
        code += 'store i8 0, i8* ' + var_name + '.last\n'
        return code

    def new_stacked(self):
        name = '%stacked' + str(len(self.stack[-1]))
        self.stack[-1].append(name)
        return name

    def new_type(self, type_def):
        self.global_types.add(type_def)
        return '%type.{:X}'.format(hash(type_def)).replace('-', 'Z')

    def generate_print(self, node):
        code  = self.generate_node(node.left);
        code += self.generate_node(node.right);

        if node.right.expr_type == ExprType.VOID:
            code += self.generate_string('void')
            code += 'call i32 @puts(i8* {}.index.0)\n'.format(self.stack[-1][-1])

        elif node.right.expr_type == ExprType.NULL:
            code += self.generate_string('null')
            code += 'call i32 @puts(i8* {}.index.0)\n'.format(self.stack[-1][-1])

        elif node.right.expr_type == ExprType.BOOLEAN:
            mem_name = self.stack[-1][-1]
            reg_name = self.new_stacked()

            code += self.generate_string('true')
            true_reg   = self.stack[-1][-1]
            true_label = self.new_stacked()

            code += self.generate_string('false')
            false_reg   = self.stack[-1][-1]
            false_label = self.new_stacked()

            end_label = self.new_stacked()

            code += '{} = load i1, i1* {}\n'.format(reg_name, mem_name)
            code += 'br i1 {}, label {}, label {}\n'.format(reg_name, true_label, false_label)
            code += '{}:\n'.format(true_label[1:])
            code += '    call i32 @puts(i8* {}.index.0)\n'.format(true_reg)
            code += '    br label {}\n'.format(end_label)
            code += '{}:\n'.format(false_label[1:])
            code += '    call i32 @puts(i8* {}.index.0)\n'.format(false_reg)
            code += '    br label {}\n'.format(end_label)
            code += '{}:\n'.format(end_label[1:])

        elif node.right.expr_type == ExprType.I32:
            mem_name = self.stack[-1][-1]
            reg_name = self.new_stacked()
            code += self.generate_string('%d\n')
            str_name = self.stack[-1][-1]
            code += '{} = load i32, i32* {}\n'.format(reg_name, mem_name)
            code += 'call i32(i8*, ...) @printf(i8* {}.index.0, i32 {})\n'.format(str_name, reg_name)

        elif node.right.expr_type == ExprType.F32:
            mem_name = self.stack[-1][-1]
            reg_name = self.new_stacked()
            code += self.generate_string('%f\n')
            str_name = self.stack[-1][-1]
            code += '{} = load float, float* {}\n'.format(reg_name, mem_name)
            code += '{}.d = fpext float {} to double\n'.format(reg_name, reg_name)
            code += 'call i32(i8*, ...) @printf(i8* {}.index.0, double {}.d)\n'.format(str_name, reg_name)

        elif node.right.expr_type == ExprType.STRING:
            message = self.stack[-1][-1]
            code += 'call i32 @puts(i8* ' + message + '.index.0)\n'

        return code

    def generate_semicolon(self, node):
        code  = self.generate_node(node.left);
        code += self.generate_node(node.right);
        return code
