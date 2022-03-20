from llvm import Function, Variable

def _decl_fn(module, name, ltype='%void', rtype='%void', ftype='%void'):
    self = Function(
        name     = module.mangle_name(name, ltype, rtype),
        args     = {},
        rtype    = module.type(ftype),
        internal = True,
    )
    module.current = self

    if ltype != '%void':
        self.args['%left'] = Variable(name='%left', type=module.type(ltype))

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


def i8_eq_i8(module):
    fn  = _decl_fn(module, '==', '%i8', '%i8', '%bool')
    reg = fn.llvm.icmp('eq', module.type('%i8').to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_lt_i32(module):
    fn  = _decl_fn(module, '<', '%i32', '%i32', '%bool')
    reg = fn.llvm.icmp('slt', module.type('%i32').to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_gt_i32(module):
    fn  = _decl_fn(module, '>', '%i32', '%i32', '%bool')
    reg = fn.llvm.icmp('sgt', module.type('%i32').to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_add_i32(module):
    fn  = _decl_fn(module, '+', '%i32', '%i32', '%i32')
    reg = fn.llvm.add(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def f32_add_f32(module):
    fn  = _decl_fn(module, '+', '%f32', '%f32', '%f32')
    reg = fn.llvm.fadd(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_sub_i32(module):
    fn  = _decl_fn(module, '-', '%i32', '%i32', '%i32')
    reg = fn.llvm.sub(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def f32_sub_f32(module):
    fn  = _decl_fn(module, '-', '%f32', '%f32', '%f32')
    reg = fn.llvm.fsub(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_mul_i32(module):
    fn  = _decl_fn(module, '*', '%i32', '%i32', '%i32')
    reg = fn.llvm.mul(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def f32_mul_f32(module):
    fn  = _decl_fn(module, '*', '%f32', '%f32', '%f32')
    reg = fn.llvm.fmul(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def i32_div_i32(module):
    fn  = _decl_fn(module, '/', '%i32', '%i32', '%i32')
    reg = fn.llvm.sdiv(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def f32_div_f32(module):
    fn  = _decl_fn(module, '/', '%f32', '%f32', '%f32')
    reg = fn.llvm.fdiv(fn.rtype.to_llvm_ir(), '%left', '%right')
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def cstrptr_at_i32(module):
    fn  = _decl_fn(module, '@', '%cstr.ptr', '%i32', '%cstr')
    ptr = fn.llvm.get_element_ptr(
        module.type('%cstr').to_llvm_ir(),
        module.type('%cstr.ptr').to_llvm_ir(), '%left',
        module.type('%i32').to_llvm_ir(),      '%right',
    )
    reg = fn.llvm.load(
        module.type('%cstr').to_llvm_ir(),
        module.type('%cstr.ptr').to_llvm_ir(),
        ptr
    )
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def cstr_at_i32(module):
    fn  = _decl_fn(module, '@', '%cstr', '%i32', '%i8')
    ptr = fn.llvm.get_element_ptr(
        module.type('%i8').to_llvm_ir(),
        module.type('%cstr').to_llvm_ir(), '%left',
        module.type('%i32').to_llvm_ir(),  '%right',
    )
    reg = fn.llvm.load(
        module.type('%i8').to_llvm_ir(),
        module.type('%cstr').to_llvm_ir(),
        ptr
    )
    fn.llvm.ret(fn.rtype.to_llvm_ir(), reg)
    return fn


def void_print_void(module):
    fn = _decl_fn(module, 'print')
    _printf(module, fn, '%s', 'void')
    return fn


def void_println_void(module):
    fn = _decl_fn(module, 'println')
    _printf(module, fn, '%s\n', 'void')
    return fn


def void_print_ptr(module):
    fn  = _decl_fn(module, 'print', rtype='%ptr')
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
    fn  = _decl_fn(module, 'println', rtype='%ptr')
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


def void_print_bool(module):
    fn = _decl_fn(module, 'print', rtype='%bool')
    fn.llvm.br_if_else('%right', 'true', 'false')

    fn.llvm.label('true')
    _printf(module, fn, '%s', 'true')
    fn.llvm.br('end')

    fn.llvm.label('false')
    _printf(module, fn, '%s', 'false')
    fn.llvm.br('end')

    fn.llvm.label('end')
    return fn


def void_println_bool(module):
    fn = _decl_fn(module, 'println', rtype='%bool')
    fn.llvm.br_if_else('%right', 'true', 'false')

    fn.llvm.label('true')
    _printf(module, fn, '%s\n', 'true')
    fn.llvm.br('end')

    fn.llvm.label('false')
    _printf(module, fn, '%s\n', 'false')
    fn.llvm.br('end')

    fn.llvm.label('end')
    return fn


def void_print_i32(module):
    fn = _decl_fn(module, 'print', rtype='%i32')
    _printf(module, fn, '%d')
    return fn


def void_println_i32(module):
    fn = _decl_fn(module, 'println', rtype='%i32')
    _printf(module, fn, '%d\n')
    return fn


def void_print_f32(module):
    fn    = _decl_fn(module, 'print', rtype='%f32')
    reg32 = fn.llvm.fpext('%right')
    reg64 = Variable(name=reg32, type=module.type('%f64'))
    _printf(module, fn, '%f', reg64)
    return fn


def void_println_f32(module):
    fn    = _decl_fn(module, 'println', rtype='%f32')
    reg32 = fn.llvm.fpext('%right')
    reg64 = Variable(name=reg32, type=module.type('%f64'))
    _printf(module, fn, '%f\n', reg64)
    return fn


def void_print_f64(module):
    fn = _decl_fn(module, 'print', rtype='%f64')
    _printf(module, fn, '%f')
    return fn


def void_println_f64(module):
    fn = _decl_fn(module, 'println', rtype='%f64')
    _printf(module, fn, '%f\n')
    return fn


def void_print_cstr(module):
    fn = _decl_fn(module, 'print', rtype='%cstr')
    _printf(module, fn, '%s')
    return fn


def void_println_cstr(module):
    fn = _decl_fn(module, 'println', rtype='%cstr')
    _printf(module, fn, '%s\n')
    return fn


