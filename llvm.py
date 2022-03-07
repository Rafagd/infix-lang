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


    def declare_variable(self, vtype, vname):
        vptr = self.alloca(vtype)
        self.scope[self.current_scope][vname] = (vtype, vptr)
        return vptr


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

