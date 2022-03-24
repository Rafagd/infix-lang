# Infix: A programming language where everything is infix.

To run your code, use the following command:
`python3 infix.py [option] <program_name> [args]`

Options are:
- --tokens: Print tokens
- --ast: Prints the AST
- --code-gen: Prints LLVM IR
- --asm: Prints the assembly instructions [ Requires lli-9 ]
- --build-only: Creates the executable, but does not run it [ Requires clang ]
- Default: Creates the executable and runs it [ Requires clang ]

Some paths are hardcoded for now: binaries are dropped in bin/, object files are dropped in obj/

Depends on Python 3 and LLVM.
