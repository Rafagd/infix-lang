#!/usr/bin/python3

import sys

from tokenizer import Tokenizer

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fpath = sys.argv[1]
    elif len(sys.argv) == 3:
        option = sys.argv[1]
        fpath  = sys.argv[2]
    else:
        print(sys.argv[0] + ' [option] <file path>')
        print('Options:')
        print('    -t : Print tokens')
        print('    -a : Print AST')
        print('    -i : Print IR (default)')
        print('    -o : Print Optimized IR')
        sys.exit(1)

    with open(fpath, 'r') as f:
        tokens = Tokenizer(f.read())
        for token in tokens:
            print(token)

