# An entire CPU emulator for my own custom design using Python.

# I know, sh*t idea. But Python is fun and slow, and my code is
# spaghetti. So they're like bread and butter. :-)

# Anyway, check 'SPECS.txt' for some epic specs information.
# This CPU design is also a little similar to the 6502, read more about it here: http://www.obelisk.me.uk/6502/

# On to the code!


import argparse

from cpu import CPU
from memory import Memory
from ins_codes import *
from screen import *
from fs import *


def main():
    screen = App()

    parser = argparse.ArgumentParser(description="A custom CPU emulator written in Python.")
    parser.add_argument("-f", "--file", help="the binary file to be loaded", required=True)
    parser.add_argument("-d", "--debug", action="store_true", help="sets the emulator into debug mode, enabling special info")
    parser.add_argument("-D", "--dump", action="store_true", help="dumps memory contents a file after running the emulator")
    parser.add_argument("-m", "--memory", help="how many bytes of memory the CPU is allocated, default is 256K", default=2**16)
    args = parser.parse_args()

    memory = Memory(args.memory)
    cpu = CPU(screen)

    if args.debug == True:
        cpu.debug = True

    try:
        with open(args.file, "r", encoding="utf-16") as f:
            data = list(f.read())
            for i, char in enumerate(data):
                memory.data[i] = ord(char)
    except OSError:
        print(f"ERR: No file named \"{args.file}\"")
        screen.callback()
        exit(1)
    except IndexError:
        print(f"ERR: Memory size too small! Cannot load file \"{args.file}\"")
        screen.callback()
        exit(1)
    except UnicodeDecodeError:
        print(f"ERR: Failed to read file \"{args.file}\", it may be corrupted")
        screen.callback()
        exit(1)

    init()

    if args.debug:
        print("Loaded virtual filesystem")

    cpu.LoadMemory(memory)
    if args.debug:
        print("Loaded memory")
        print("Executing...")
    cpu.Execute()

    #* This is some code used to dump the memory into a file for easier running and turning code into an executable *#
    if args.dump:
        f = open("dump.mem", "a", encoding="utf-16")
        for dat in memory.data:
            f.write(chr(dat))
        f.close()

        if args.debug:
            print("Dumped memory")


if __name__ == "__main__":
    main()
    print() # Prints a new line to not screw up some terminals