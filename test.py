#!/usr/bin/python3

import sys
import os
import subprocess

def run_test(test_name, max_file_name, output=False):
    try:
        with open('tests/{}.args'.format(test_name), 'r') as args_file:
            args = args_file.read()
    except:
        args = ''
    
    try:
        process_out = subprocess.check_output('python3 infix.py tests/{}.ifx 2> /dev/null | lli-9 {} 2> /dev/null'.format(test_name, args.strip()), stderr=None, shell=True)
        process_out = process_out.decode('UTF-8')
    except Exception as e:
        if output:
            print(e)
        print('{fname:{fill}} [FAILURE] Finished with non-zero exit status'.format(fname=test_name + ':', fill=max_file_name))
        return

    try:
        with open('tests/{}.out'.format(test_name), 'r') as expected_file:
            expected_out = expected_file.read()
    except:
        print('{fname:{fill}} [FAILURE] Missing expected output file'.format(fname=test_name + ':', fill=max_file_name))
        return

    if process_out != expected_out:
        print('{fname:{fill}} [FAILURE] Process output does not match expected output'.format(fname=test_name + ':', fill=max_file_name))
    else:
        print('{fname:{fill}} [SUCCESS]'.format(fname=test_name + ':', fill=max_file_name))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_test(sys.argv[1], len(sys.argv[1]) + 1, output=True)
    else:
        max_file_name = 1 + max([ len(f) for f in os.listdir('tests/') if f[-3:] == 'ifx' ])
        for test_file in os.listdir('tests/'):
            if test_file[-3:] != 'ifx':
                continue
            run_test(test_file[:-4], max_file_name)

