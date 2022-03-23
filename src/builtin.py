from src.llvm import Function, Variable

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


def ptr_eq_ptr(module):
    fn  = _decl_fn(module, '==', '%ptr', '%ptr', '%bool')
    reg = fn.llvm.icmp('eq', module.type('%ptr').to_llvm_ir(), '%left', '%right')
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


