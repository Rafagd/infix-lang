from __future__  import annotations

import struct

from dataclasses import dataclass
from inspect     import getmembers, isfunction

class LLVMError(Exception):
    pass

class LLVMTypeError(Exception):
    pass

class CommentContext:
    def __init__(self, llvm, comment, *args):
        self.llvm    = llvm
        self.comment = comment
        self.args    = args

    def __enter__(self):
        self.llvm.comment(self.comment, *self.args)

    def __exit__(self, *exception):
        self.llvm.line('')

class DefineContext:
    def __init__(self, llvm, internal, rtype, name, *args, **kwargs):
        self.llvm     = llvm
        self.rtype    = rtype
        self.name     = name
        self.internal = internal
        self.args     = args


    def __enter__(self):
        args = ''
        for i in range(0, len(self.args), 2):
            args += self.args[i] + ' ' + self.args[i+1] + ', '
        self.llvm.line('define {} {} {}({})', 
            'internal' if self.internal else 'external',
            self.rtype,
            self.name,
            args[:-2]
        )
        self.llvm.line('{')

    def __exit__(self, *exception):
        self.llvm.line('}')

class LLVM:
    def __init__(self):
        self.last_reg = 0
        self.last_lbl = 0
        self.code     = ''

    def line(self, line, *args):
        if len(args) > 0:
            self.code += line.format(*args) + '\n'
        else:
            self.code += line + '\n'

    def comment(self, comment, *args):
        self.line('; ' + comment, *args)

    def commented_block(self, comment, *args):
        return CommentContext(self, comment, *args)

    def next_lbl(self):
        self.last_lbl += 1
        return 'lbl' + str(self.last_lbl)

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

    def define(self, internal, name, rtype, *args):
        return DefineContext(self, internal, rtype, name, *args)

    def instr(self, instruction, *args):
        self.line(4 * ' ' + instruction, *args)

    def next_reg(self):
        self.last_reg += 1
        return '%reg' + str(self.last_reg)

    def alloca(self, type, reg=None):
        if reg is None:
            reg = self.next_reg()
        self.instr('{} = alloca {}', reg, type)
        return reg

    def malloc(self, type, elems=None):
        reg = self.next_reg()
        if elems is None:
            self.instr('{} = malloc {}', reg, type)
        else:
            self.instr('{} = malloc {}, i64 {}', reg, type, elems)
        return reg

    def free(self, type, reg):
        self.instr('free {} {}', type, reg)
        return reg

    def get_element_ptr(self, rtype, ptype, pname, *args):
        reg   = self.next_reg()
        instr = '{} = getelementptr {}, {} {}' + ', {} {}' * (len(args) // 2)
        self.instr(instr, reg, rtype, ptype, pname, *args)
        return reg

    def load(self, store_type, value_type, value):
        reg = self.next_reg()
        self.instr('{} = load {}, {} {}', reg, store_type, value_type, value)
        return reg

    def store(self, rtype, rname, ptype, pname):
        self.instr('store {} {}, {} {}', rtype, rname, ptype, pname)

    def fpext(self, from_type, to_type, value):
        reg = self.next_reg()
        self.instr('{} = fpext {} {} to {}', reg, from_type, value, to_type)
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

    def ret(self, type, reg=None):
        if reg is None:
            self.instr('ret {}'.format(type))
        else:
            self.instr('ret {} {}'.format(type, reg))

    def br_if_else(self, cdreg, tlabel, flabel):
        self.instr('br i1 {}, label %{}, label %{}', cdreg, tlabel, flabel)

    def br(self, label):
        self.instr('br label %{}', label)

    def label(self, name):
        self.line(name + ':')

    def icmp(self, op, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = icmp {} {} {}, {}', reg, op, rtype, a, b)
        return reg

    def add(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = add {} {}, {}', reg, rtype, a, b)
        return reg

    def fadd(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = fadd {} {}, {}', reg, rtype, a, b)
        return reg

    def sub(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = sub {} {}, {}', reg, rtype, a, b)
        return reg

    def fsub(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = fsub {} {}, {}', reg, rtype, a, b)
        return reg

    def mul(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = mul {} {}, {}', reg, rtype, a, b)
        return reg

    def fmul(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = fmul {} {}, {}', reg, rtype, a, b)
        return reg

    def sdiv(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = sdiv {} {}, {}', reg, rtype, a, b)
        return reg

    def fdiv(self, rtype, a, b):
        reg = self.next_reg()
        self.instr('{} = fdiv {} {}, {}', reg, rtype, a, b)
        return reg


class ProgramError(Exception):
    pass

class ProgramTypeError(ProgramError):
    pass

class ProgramUnknownOperationError(ProgramError):
    pass

@dataclass
class Type:
    name:      str
    repr:      str
    primitive: bool = False

    def __post_init__(self):
        if self.name[0] != '%':
            raise LLVMTypeError('Type names MUST start with %')

    def ptr(self):
        return Type(
            self.name + '.ptr',
            self.repr + '*',
            primitive=True
        )

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
        if type is None:
            raise LLVMTypeError('Variables MUST have a type')

        if self.type.name == '%void':
            self.name = '%void'

        if self.name[0] not in [ '%', '@' ]:
            raise LLVMTypeError('Variable names MUST start with % or @')

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.value is None:
            return '{{{}: {}}}'.format(self.name, self.type.to_llvm_ir())
        else:
            return '{{{}: {} = {}}}'.format(self.name, self.type.to_llvm_ir(), self.value)



@dataclass
class Function:
    name:      str
    llvm:      LLVM           = None
    args:      Dict[Variable] = None
    rtype:     Type           = None
    variables: Dict[Variable] = None
    internal:  bool           = False
    used:      bool           = False

    def __post_init__(self):
        if self.name[0] != '@':
            raise LLVMTypeError('Operation names MUST start with @')

        if self.llvm is None:
            self.llvm = LLVM()

        if self.args is None:
            self.args = {}

        if self.variables is None:
            self.variables = {}

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.name + ' -> ' + self.rtype.name


@dataclass
class External:
    name:  str
    rtype: Type
    args:  List[Type] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []

@dataclass
class Module:
    llvm:      LLVM           = None
    types:     Dict[Type]     = None
    variables: Dict[Variable] = None
    externals: Dict[External] = None
    functions: Dict[Function] = None

    current = None

    def __post_init__(self):
        if self.llvm      is None: self.llvm      = LLVM()
        if self.types     is None: self.types     = {}
        if self.variables is None: self.variables = {}
        if self.externals is None: self.externals = {}
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
        self.new_type('%vararg', '...',  primitive=True) # vararg for externs
        self.new_type('%cstr',     'i8*')
        self.new_type('%cstr.ptr', 'i8**')
        self.new_type('%list.i8',  '{ i64, i8* }')
        self.new_type('%list.i32',  '{ i64, i8* }')

    def default_variables(self):
        self.const_cstr('%s\n')

    def default_operations(self):
        import src.builtin # to avoid circular import

        for name, fn in getmembers(src.builtin, isfunction):
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
            rtype = self.type('%i32'),
            used  = True,
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

    def new_global_var(self, name, type, value):
        if name not in self.variables:
            self.variables[name] = Variable(name=name, type=type, value=value)
        else:
            raise ProgramTypeError('Duplicated variable: ' + name)
        return self.variables[name]
    
    def global_var(self, name):
        try:
            return self.variables[name]
        except KeyError:
            raise ProgramError('Undeclared variable: ' + name)

    def new_variable(self, name, type):
        with self.current.llvm.commented_block('new {}', name):
            if name in self.current.args or name in self.current.variables:
                raise ProgramTypeError('Duplicated variable: ' + name)

            if name in [ '%left', '%right' ]:
                self.current.args[name] = Variable(name=name, type=type)
                return self.current.args[name]

            reg = self.current.llvm.alloca(type.to_llvm_ir(), reg=name)
            self.current.variables[name] = Variable(name=reg, type=type)
            return self.current.variables[name]
    
    def ptr_to(self, name):
        with self.current.llvm.commented_block('ptr-to {}', name):
            # Try to find a local-scope variable
            try:                            
                reg = self.current.variables[name]
                return Variable(reg.name, reg.type.ptr())
            except KeyError:
                raise

    def variable(self, name):
        with self.current.llvm.commented_block('variable {}', name):
            # Try to find a local-scope variable
            try:                            
                ptr = self.current.variables[name]
                reg = self.current.llvm.load(
                    ptr.type.to_llvm_ir(),
                    ptr.type.to_llvm_ir() + '*',
                    ptr.name
                )
                return Variable(name=reg, type=ptr.type)
            except KeyError:
                pass

            # Try to find an argument variable
            try:
                return self.current.args[name]
            except KeyError:
                pass
            
            # Finally, try a global-scope variable or fail
            return self.global_var(name)

    def add_external(self, name, rtype, args):
        if name in self.externals:
            return
        self.externals[name] = External(
            name  = name,
            rtype = self.type(rtype),
            args  = [ self.type(arg) for arg in args ]
        )

    def call_external(self, name, args):
        if name not in self.externals:
            raise ProgramUnknownOperationError('Unknown external')

        a = []
        for arg in args:
            a.append(arg.type.to_llvm_ir())
            a.append(arg.name)
        
        external = self.externals[name]
        extype   = external.rtype.to_llvm_ir()

        if any(arg.name == '%vararg' for arg in external.args):
            extype += '(' + ', '.join(arg.to_llvm_ir() for arg in external.args) + ')'

        ret = self.current.llvm.call(extype, name, *a)
        return Variable(ret, external.rtype)

    def cast(self, name, type):
        var   = self.variable(name)
        tfrom = var.type
        tto   = self.type('%f64')
        with self.current.llvm.commented_block('cast {} to {}'.format(tfrom.name, tto.name)):
            if var.type.name[1] == 'f':
                ret = self.current.llvm.fpext(tfrom.to_llvm_ir(), tto.to_llvm_ir(), var.name)
                return Variable(ret, tto)
        raise Exception('Unsupported cast {} to {}'.format(tfrom.name, tto.name))


    def const(self, type, value):
        index = type.name + ';' + value

        try:
            return self.const_regs[index]

        except KeyError:
            self.last_const_reg += 1
            self.const_regs[index] = self.new_global_var(
                name  = '@const.{}'.format(self.last_const_reg),
                type  = type,
                value = value
            )
            return self.const_regs[index]

    def deref_ptr(self, ptr):
        with self.current.llvm.commented_block('deref {}', ptr.name):
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def assign(self, pname, reg):
        with self.current.llvm.commented_block('{} = {}', pname, reg):
            self.current.llvm.store(
                reg.type.to_llvm_ir(),       reg.name,
                reg.type.to_llvm_ir() + '*', pname,
            )
            return reg

    def const_ptr(self, value):
        with self.current.llvm.commented_block('ptr {}', value):
            ptr = self.const(self.type('%ptr'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_bool(self, value):
        with self.current.llvm.commented_block('bool {}', value):
            ptr = self.const(self.type('%bool'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_i32(self, value):
        with self.current.llvm.commented_block('i32 {}', value):
            ptr = self.const(self.type('%i32'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_f32(self, value):
        with self.current.llvm.commented_block('f32 {}', value):
            value = struct.unpack('@Q', struct.pack('@d', float(value)))[0]
            value = '0x{:X}'.format(value & 0xFFFF_FFFF_E000_0000)

            ptr = self.const(self.type('%f32'), value)
            reg = self.current.llvm.load(
                ptr.type.to_llvm_ir(),
                ptr.type.to_llvm_ir() + '*',
                ptr.name
            )
            return Variable(name=reg, type=ptr.type)

    def const_cstr(self, value):
        size  = len(value) + 1 # + \0
        value = value.replace('\n', '\\0A')

        with self.current.llvm.commented_block('string "{}"', value):
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

    def new_list(self, values):
        type = values[0].type if len(values) > 0 else self.type('%i8')

        with self.current.llvm.commented_block('list of {} {}s', len(values), type.name):
            tname = '%list.{}'.format(type.name.replace('%', ''))
            stype = self.type(tname, '[ i64, i64, {}* ]'.format(type.to_llvm_ir()))

            lst = self.const(stype, '[ i64 {len}, i64 {len}, {type}* null ]'.format(len=len(values), type=type.to_llvm_ir()))
            ptr = self.current.llvm.malloc(type.to_llvm_ir, len(values))
            return lst

    def new_struct(self, value):
        return Variable(type=self.type('%void'))

    def mangle_name(self, fname, ltype, rtype):
        if len(fname) > 1:
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
            func.used = True
        except:
            raise ProgramUnknownOperationError('Unknown operation: {}'.format(call_name))

        with self.current.llvm.commented_block(call_name):
            reg = self.current.llvm.call(func.rtype.to_llvm_ir(), call_name, *args)
            return Variable(name=reg, type=func.rtype)

    def ret(self, reg):
        if reg.type.name == '%void':
            self.current.rtype = reg.type
            self.current.llvm.ret(reg.type.to_llvm_ir())
        else:
            self.current.rtype = reg.type
            self.current.llvm.ret(reg.type.to_llvm_ir(), reg.name)

    def function(self, name):
        class Fn:
            def __init__(self, module, name):
                self.module = module
                self.name   = name

                self.function = Function(
                    name = name,
                    args = {},
                    rtype = module.type('%void'),
                )

            def __enter__(self):
                self.previous       = self.module.current
                self.module.current = self.function
                return self

            def __exit__(self, *_):
                try:
                    left = self.function.args['%left']
                except KeyError: 
                    left = Variable(type=self.module.type('%void'))

                try:
                    right = self.function.args['%right']
                except KeyError: 
                    right = Variable(type=self.module.type('%void'))

                self.function.name = self.module.mangle_name(
                    self.name, left.type.name, right.type.name
                )
    
                self.module.functions[self.function.name] = self.function
                self.module.current = self.previous

        return Fn(self, name)

    def if_then(self, cond):
        class IfThen:
            def __init__(self, llvm, cond):
                self.llvm = llvm
                self.cond = cond
                self.tlbl = llvm.next_lbl()
                self.flbl = llvm.next_lbl()

            def __enter__(self):
                self.llvm.comment('if')
                self.llvm.br_if_else(self.cond.name, self.tlbl, self.flbl)
                self.llvm.label(self.tlbl)
                return self

            def __exit__(self, *_):
                self.llvm.br(self.flbl)
                self.llvm.label(self.flbl)
                self.llvm.line('')

        return IfThen(self.current.llvm, cond)

    def loop(self):
        class Loop:
            def __init__(self, llvm):
                self.llvm = llvm
                self.slbl = llvm.next_lbl()
                self.elbl = llvm.next_lbl()

            def __enter__(self):
                self.llvm.comment('repeat')
                self.llvm.br(self.slbl)
                self.llvm.label(self.slbl)
                return self

            def __exit__(self, *_):
                self.llvm.br(self.slbl)
                self.llvm.label(self.elbl)
                self.llvm.line('')

            def end(self):
                self.llvm.br(self.elbl)

        return Loop(self.current.llvm)

    def negate(self, value):
        reg = self.current.llvm.icmp('eq', 'i1', value.name, '0')
        return Variable(name=reg, type=self.type('%bool'))

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
            for _, ex in self.externals.items():
                self.llvm.declare(ex.name, ex.rtype.to_llvm_ir(), *[
                    arg.to_llvm_ir() for arg in ex.args
                ])

        with self.llvm.commented_block('Functions:'):
            for _, fn in self.functions.items():
                if not fn.used:
                    continue
                args = []
                for _, arg in fn.args.items():
                    args.append(arg.type.to_llvm_ir())
                    args.append(arg.name)
                with self.llvm.define(fn.internal, fn.name, fn.rtype.to_llvm_ir(), *args):
                    self.llvm.code += fn.llvm.code
                    if fn.name == '@main':
                        self.llvm.ret(self.type('%i32').to_llvm_ir(), '0')
                self.llvm.line('')

        return self.llvm.code


