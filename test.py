#!/usr/bin/python3

import sys
import os
import subprocess

max_file_name = 1 + max([
    len(fname) for fname in os.listdir('tests/') if fname[-3:] == 'ifx'
])

for test_file in os.listdir('tests/'):
    if test_file[-3:] != 'ifx':
        continue

    test_name = test_file[:-4]

    try:
        with open('tests/{}.args'.format(test_name), 'r') as args_file:
            args = args_file.read()
    except:
        args = ''
    
    try:
        process_out = subprocess.check_output('python3 infix.py tests/{}.ifx 2> /dev/null | lli-9 {} 2> /dev/null'.format(test_name, args.strip()), stderr=None, shell=True)
        process_out = process_out.decode('UTF-8')
    except Exception as e:
        print(e)
        print('{fname:{fill}} [FAILURE] Finished with non-zero exit status'.format(fname=test_file + ':', fill=max_file_name))
        continue

    try:
        with open('tests/{}.out'.format(test_name), 'r') as expected_file:
            expected_out = expected_file.read()
    except:
        print('{fname:{fill}} [FAILURE] Missing expected output file'.format(fname=test_file + ':', fill=max_file_name))
        continue

    if process_out != expected_out:
        print('{fname:{fill}} [FAILURE] Process output does not match expected output'.format(fname=test_file + ':', fill=max_file_name))
    else:
        print('{fname:{fill}} [SUCCESS]'.format(fname=test_file + ':', fill=max_file_name))


