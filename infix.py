#!/usr/bin/python3

import re
import sys

from pathlib import Path

from src.tokenizer import Tokenizer
from src.parser    import Parser, print_ast
from src.generator import Generator

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1][0] != '-':
            option = None
            fpath  = sys.argv[1]
            args   = sys.argv[2:]
        else:
            option = sys.argv[1]
            fpath  = sys.argv[2]
            args   = sys.argv[3:]
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
        full_text  = '#include std.ifx\n'
        full_text += f.read()

    included = set()
    while includes := re.findall('\s*#include\s+(.*)', full_text):
        for include in includes:
            resolved = str(Path('include/' + include).resolve())
            if resolved in included:
                full_text = re.sub('\s*#include\s+' + include, '', full_text)
            else:
                with open(resolved, 'r') as f:
                    full_text = re.sub('\s*#include\s+' + include, f.read(), full_text)
                    included.add(resolved)

    tokens = Tokenizer(full_text)

    if option == '--tokens':
        for token in tokens:
            print(token)
        sys.exit(0)

    ast = Parser(tokens).parse()

    if option == '--ast':
        print_ast(ast)
        sys.exit(0)

    ir_repr = Generator().generate(ast)

    if option == '--type-checker':
        print_ast(ast)
        sys.exit(0)

    if option == '--code-gen':
        print(ir_repr)
        sys.exit(0)

    import os
    from subprocess import Popen, PIPE

    if option == '--asm':
        process = [ 'llc-9' ]
    else:
        process = [ 'llc-9', '-filetype=obj', '-o', fpath.replace('.ifx', '.o') ]

    with Popen(process, stdin=PIPE, stdout=PIPE) as llc:
        out, err = llc.communicate(bytes(ir_repr, 'utf-8'))
        if err is not None:
            print(str(err, 'utf-8'))
            sys.exit(1)

    if option == '--asm':
        print(str(out, 'utf-8'))
        sys.exit(0)

    with Popen(['clang', fpath.replace('.ifx', '.o'), '-o', fpath.replace('.ifx', '') ], stdin=PIPE, stdout=PIPE) as clang:
        out, err = clang.communicate(out)
        if err is not None:
            print(str(err, 'utf-8'))
            sys.exit(1)

    if option == '--build-only':
        sys.exit(0)

    os.system(fpath.replace('.ifx', '') + ' ' + ' '.join(args))
    

