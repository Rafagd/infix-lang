#!/usr/bin/python3

import sys

from tokenizer import Tokenizer
from parser    import Parser, print_ast
from type_checker import TypeChecker
from generator import Generator

if __name__ == '__main__':
    if len(sys.argv) == 2:
        option = None
        fpath  = sys.argv[1]
    elif len(sys.argv) == 3:
        option = sys.argv[1]
        fpath  = sys.argv[2]
    else:
        print(sys.argv[0] + ' [option] <file path>')
        print('Options:')
        print('    --tokens       : Prints the tokens')
        print('    --ast          : Prints the AST')
        print('    --type-checker : Prints the tagged AST')
        print('    --code-gen     : Print IR (default)')
#        print('    -o : Print Optimized IR')
        sys.exit(1)

    with open(fpath, 'r') as f:
        tokens = Tokenizer(f.read())

    if option == '--tokens':
        for token in tokens:
            print(token)
        sys.exit(0)

    ast = Parser(tokens).parse()

    if option == '--ast':
        print_ast(ast)
        sys.exit(0)

    type_checker = TypeChecker()
    ast = type_checker.check(ast)

    if option == '--type-checker':
        print_ast(ast)
        sys.exit(0)

    ir_repr = Generator(type_checker.var_defs, type_checker.ops_defs).generate(ast)

    if True or option == '--code-gen':
        print(ir_repr)

