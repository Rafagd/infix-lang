from llvm import Function, Variable

def _decl_fn(module, name, rtype):
    self = Function(
        name  = module.mangle_name(name, '%void', rtype),
        args  = {},
        rtype = module.type('%void'),
    )
    module.current = self

    if rtype != '%void':
        self.args['%right'] = Variable(name='%right', type=module.type(rtype))

    return self

def _printf(module, fn, pattern, value=None):
    pattern = module.const_cstr(pattern)

    if value is None:
        rtype = fn.args['%right'].type.to_llvm_ir()
        rreg  = '%right'
    elif isinstance(value, Variable):
        rtype = value.type.to_llvm_ir()
        rreg  = value.name
    else:
        rtype = '%cstr'
        rreg  = module.const_cstr(value).name

    fn.llvm.call('i32(%cstr, ...)', '@printf', '%cstr', pattern.name, rtype, rreg)


def void_print_void(module):
    fn = _decl_fn(module, 'print', '%void')
    _printf(module, fn, '%s', 'void')
    return fn


def void_println_void(module):
    fn = _decl_fn(module, 'println', '%void')
    _printf(module, fn, '%s\n', 'void')
    return fn


def void_print_ptr(module):
    fn  = _decl_fn(module, 'print', '%ptr')
    reg = fn.llvm.icmp('eq', 'i8*', '%right', 'null')
    fn.llvm.br_if_else(reg, 'is_null', 'not_null')

    fn.llvm.label('is_null')
    _printf(module, fn, '%s', 'null')
    fn.llvm.br('end')

    fn.llvm.label('not_null')
    _printf(module, fn, '0x%08X')
    fn.llvm.br('end')

    fn.llvm.label('end')
    return fn


def void_println_ptr(module):
    fn  = _decl_fn(module, 'println', '%ptr')
    reg = fn.llvm.icmp('eq', 'i8*', '%right', 'null')
    fn.llvm.br_if_else(reg, 'is_null', 'not_null')

    fn.llvm.label('is_null')
    _printf(module, fn, '%s\n', 'null')
    fn.llvm.br('end')

    fn.llvm.label('not_null')
    _printf(module, fn, '0x%08X\n')
    fn.llvm.br('end')

    fn.llvm.label('end')
    return fn


def void_print_i32(module):
    fn = _decl_fn(module, 'print', '%i32')
    _printf(module, fn, '%d')
    return fn


def void_println_i32(module):
    fn = _decl_fn(module, 'println', '%i32')
    _printf(module, fn, '%d\n')
    return fn


def void_print_f32(module):
    fn    = _decl_fn(module, 'print', '%f32')
    reg32 = fn.llvm.fpext('%right')
    reg64 = Variable(name=reg32, type=module.type('%f64'))
    _printf(module, fn, '%f', reg64)
    return fn


def void_println_f32(module):
    fn    = _decl_fn(module, 'println', '%f32')
    reg32 = fn.llvm.fpext('%right')
    reg64 = Variable(name=reg32, type=module.type('%f64'))
    _printf(module, fn, '%f\n', reg64)
    return fn


def void_print_f64(module):
    fn = _decl_fn(module, 'print', '%f64')
    _printf(module, fn, '%f')
    return fn


def void_println_f64(module):
    fn = _decl_fn(module, 'println', '%f64')
    _printf(module, fn, '%f\n')
    return fn


def void_print_cstr(module):
    fn = _decl_fn(module, 'print', '%cstr')
    _printf(module, fn, '%s')
    return fn


def void_println_cstr(module):
    fn = _decl_fn(module, 'println', '%cstr')
    _printf(module, fn, '%s\n')
    return fn


