from __future__  import annotations
from dataclasses import dataclass

import struct

class LLVMError(Exception):
    pass

class LLVMTypeError(Exception):
    pass

class CommentContext:
    def __init__(self, llvm, comment):
        self.llvm    = llvm
        self.comment = comment

    def __enter__(self):
        self.llvm.comment(self.comment)

    def __exit__(self, *exception):
        self.llvm.line('')

class DefineContext:
    def __init__(self, llvm, rtype, name, *args):
        self.llvm  = llvm
        self.rtype = rtype
        self.name  = name
        self.args  = args

    def __enter__(self):
        args = ''
        for i in range(0, len(self.args), 2):
            args += self.args[i] + ' ' + self.args[i+1] + ', '
        self.llvm.line('define {} {}({})', self.rtype, self.name, args[:-2])
        self.llvm.line('{')

    def __exit__(self, *exception):
        if self.rtype == 'void':
            self.llvm.instr('ret void')
        self.llvm.line('}')

class LLVM:
    def __init__(self):
        self.last_reg = 0
        self.code     = ''

    def line(self, line, *args):
        if len(args) > 0:
            self.code += line.format(*args) + '\n'
        else:
            self.code += line + '\n'

    def comment(self, comment):
        self.line('; ' + comment)

    def commented_block(self, comment):
        return CommentContext(self, comment)

    def label(self, label_name):
        self.line(label_name + ':')

    def type(self, name, llvm_type):
        self.line('{} = type {}', name, llvm_type)

    def global_variable(self, name, vtype, value=None):
        if value is None:
            self.line('{} = constant {}', name, vtype)
        else:
            self.line('{} = constant {} {}', name, vtype, value)

    def declare(self, name, rtype, *args):
        argptrn = ', '.join([ '{}' for _ in args ])
        self.line('declare {} {}(' + argptrn + ')', rtype, name, *args)

    def define(self, name, rtype, *args):
        return DefineContext(self, rtype, name, *args)

    def instr(self, instruction, *args):
        self.line(4 * ' ' + instruction, *args)

    def next_reg(self):
        self.last_reg += 1
        return '%' + str(self.last_reg)

    def get_element_ptr(self, rtype, ptype, pname, *args):
        reg   = self.next_reg()
        instr = '{} = getelementptr {}, {} {}' + ', {} {}' * (len(args) // 2)
        self.instr(instr, reg, rtype, ptype, pname, *args)
        return reg

    def load(self, store_type, value_type, value):
        reg = self.next_reg()
        self.instr('{} = load {}, {} {}', reg, store_type, value_type, value)
        return reg

    def fpext(self, f32_reg):
        reg = self.next_reg()
        self.instr('{} = fpext float {} to double', reg, f32_reg)
        return reg

    def call(self, ftype, fname, *args):
        argptrn = ', '.join([ '{} {}' for _ in range(0, len(args), 2) ])

        if ftype != 'void':
            reg     = self.next_reg()
            instr   = '{} = call {} {}(' + argptrn + ')'
            self.instr(instr, reg, ftype, fname, *args)
            return reg
        else:
            instr   = 'call {} {}(' + argptrn + ')'
            self.instr(instr, ftype, fname, *args)
            return None

    def ret(self, rret):
        self.instr('ret {}'.format(rret))

    def br_if_else(self, cdreg, tlabel, flabel):
        self.instr('br i1 {}, label %{}, label %{}', cdreg, tlabel, flabel)

    def br(self, label):
        self.instr('br label %{}', label)

    def label(self, name):
        self.line(name + ':')

    def icmp(self, op, rtype, areg, breg):
        reg = self.next_reg()
        self.instr('{} = icmp {} {} {}, {}', reg, op, rtype, areg, breg)
        return reg


class ProgramError(Exception):
    pass

class ProgramTypeError(Exception):
    pass


@dataclass
class Type:
    name:      str
    repr:      str
    primitive: bool = False

    def __post_init__(self):
        if self.name[0] != '%':
            raise LLVMTypeError('Type names MUST start with %')

    def to_llvm_ir(self):
        if self.primitive:
            return self.repr
        else:
            return self.name


@dataclass
class Variable:
    name:     str  = None
    type:     Type = None
    value:    str  = None
    implicit: bool = False

    def __post_init__(self):
        if self.name[0] not in [ '%', '@' ]:
            raise LLVMTypeError('Type names MUST start with % or @')

    def __repr__(self):
        if self.value is None:
            return '{{{}: {}}}'.format(self.name, self.type.to_llvm_ir())
        else:
            return '{{{}: {} = {}}}'.format(self.name, self.type.to_llvm_ir(), self.value)



@dataclass
class Function:
    name:   str
    llvm:   LLVM              = None
    args:   Dict[Variable]    = None
    rtype:  Type              = None
    instrs: List[Instruction] = None

    def __post_init__(self):
        if self.name[0] != '@':
            raise LLVMTypeError('Operation names MUST start with @')
        if self.llvm is None:
            self.llvm = LLVM()


@dataclass
class Module:
    llvm:      LLVM           = None
    types:     Dict[Type]     = None
    variables: Dict[Variable] = None
    functions: Dict[Function] = None

    current = None

    def __post_init__(self):
        if self.llvm      is None: self.llvm      = LLVM()
        if self.types     is None: self.types     = {}
        if self.variables is None: self.variables = {}
        if self.functions is None: self.functions = {}

        self.last_const_reg = 0
        self.const_regs     = {}

        self.default_types()
        self.default_operations()
        self.default_variables()

    def default_types(self):
        self.new_type('%void', 'void',   primitive=True)
        self.new_type('%ptr',  'i8*',    primitive=False)
        self.new_type('%bool', 'i1',     primitive=True)
        self.new_type('%i8',   'i8',     primitive=True)
        self.new_type('%i16',  'i16',    primitive=True)
        self.new_type('%i32',  'i32',    primitive=True)
        self.new_type('%i64',  'i64',    primitive=True)
        self.new_type('%f16',  'half',   primitive=True)
        self.new_type('%f32',  'float',  primitive=True)
        self.new_type('%f64',  'double', primitive=True)
        self.new_type('%f128', 'fp128',  primitive=True)
        self.new_type('%cstr',     'i8*')
        self.new_type('%cstr.ptr', 'i8**')

    def default_variables(self):
        self.const_cstr('%s\n')

    def default_operations(self):
        import builtin
        from inspect import getmembers, isfunction

        for name, fn in getmembers(builtin, isfunction):
            if name[0] == '_':
                continue
            fn_def = fn(self)
            self.functions[fn_def.name] = fn_def

        self.functions['@main'] = Function(
            name = '@main',
            args = {
                '%argc' : Variable(name='%argc', type=self.type('%i32')),
                '%argv' : Variable(name='%argv', type=self.type('%cstr.ptr')),
            },
            rtype = self.type('%void'),
        )

        self.current = self.functions['@main']

    def new_type(self, name, repr, primitive=False):
        if name not in self.types:
            self.types[name] = Type(name=name, repr=repr, primitive=primitive)
        else:
            raise ProgramTypeError('Duplicated type: ' + name)
        return self.types[name]

    def type(self, name, repr=None, primitive=False):
        try:
            return self.types[name]
        except KeyError:
            if repr is None:
                raise ProgramTypeError('Undeclared type: ' + name)
            return self.new_type(name, repr, primitive)

    def new_variable(self, name, type, value):
        if name not in self.variables:
            self.variables[name] = Variable(name=name, type=type, value=value)
        else:
            raise ProgramTypeError('Duplicated variable: ' + name)
        return self.variables[name]
    
    def variable(self, name):
        try:
            return self.variables[name]
        except KeyError:
            raise ProgramError('Undeclared variable: ' + name)

    def const(self, type, value):
        index = type.name + ';' + value

        try:
            return self.const_regs[index]

        except KeyError:
            self.last_const_reg += 1
            self.const_regs[index] = self.new_variable(
                name  = '@const.{}'.format(self.last_const_reg),
                type  = type,
                value = value
            )
            return self.const_regs[index]

    def const_ptr(self, value):
        with self.current.llvm.commented_block('ptr ' + value):
            ptr = self.const(self.type('%ptr'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_cstr(self, value):
        size  = len(value) + 1 # + \0
        value = value.replace('\n', '\\0A')

        with self.current.llvm.commented_block('string "{}"'.format(value)):
            tname = '%cstr.{}'.format(size)
            stype = self.type(tname, '[ {} x i8 ]'.format(size))

            ptr = self.const(stype, 'c"{}\\00"'.format(value))
            reg = self.current.llvm.get_element_ptr(
                stype.to_llvm_ir(),
                stype.to_llvm_ir() + '*',
                ptr.name,
                'i64', 0, 'i64', 0
            )
            return Variable(name=reg, type=self.type('%cstr'))

    def const_f32(self, value):
        with self.current.llvm.commented_block('f32 {}'.format(value)):
            value = struct.unpack('@Q', struct.pack('@d', float(value)))[0]
            value = '0x{:X}'.format(value & 0xFFFF_FFFF_E000_0000)

            ptr = self.const(self.type('%f32'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_i32(self, value):
        with self.current.llvm.commented_block('i32 {}'.format(value)):
            ptr = self.const(self.type('%i32'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def mangle_name(self, fname, ltype, rtype):
        fname = fname.replace('"', '\\"').replace('%', '').replace('@', '')
        ltype = ltype.replace('"', '\\"').replace('%', '').replace('@', '')
        rtype = rtype.replace('"', '\\"').replace('%', '').replace('@', '')
        return '@"{};{};{}"'.format(ltype, fname, rtype)

    def call(self, fname, larg=None, rarg=None):
        args  = []
        ltype = '%void'
        if larg is not None and larg.type.name != '%void':
            ltype = larg.type.name
            args.append(larg.type.to_llvm_ir())
            args.append(larg.name)

        rtype = '%void'
        if rarg is not None and rarg.type.name != '%void':
            rtype = rarg.type.name
            args.append(rarg.type.to_llvm_ir())
            args.append(rarg.name)

        call_name = self.mangle_name(fname, ltype, rtype)

        try:
            func = self.functions[call_name]
        except:
            return
            raise Exception('Unknown operation: {}'.format(call_name))

        with self.current.llvm.commented_block(call_name):
            ret_reg = self.current.llvm.call(func.rtype.to_llvm_ir(), call_name, *args)
            return ret_reg

    def to_llvm_ir(self):
        with self.llvm.commented_block('Declared types:'):
            for _, ty in self.types.items():
                if ty.primitive:
                    continue
                self.llvm.type(ty.name, ty.repr)

        with self.llvm.commented_block('Globals and constants:'):
            for _, vr in self.variables.items():
                self.llvm.global_variable(vr.name, vr.type.to_llvm_ir(), vr.value)

        with self.llvm.commented_block('Externals'):
            self.llvm.declare('@printf', 'i32', 'i8*', '...')

        with self.llvm.commented_block('Functions:'):
            for _, fn in self.functions.items():
                args = []
                for _, arg in fn.args.items():
                    args.append(arg.type.to_llvm_ir())
                    args.append(arg.name)
                with self.llvm.define(fn.name, fn.rtype.to_llvm_ir(), *args):
                    self.llvm.code += fn.llvm.code
                self.llvm.line('')

        return self.llvm.code


"""
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

    def declare_variable(self, vtype, vname):
        vptr = self.alloca(vtype)
        self.scope[self.current_scope][vname] = (vtype, vptr)
        return vptr

    def type(self, declaration):
        try:
            type_reg = self.declared[hash(declaration)]
        except:
            type_reg      = self.new_type()
            self.globals += '{} = type {}\n'.format(type_reg, declaration)
            self.declared[hash(declaration)] = type_reg
        return type_reg


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
"""


