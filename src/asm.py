import argparse
import sys
import os

from typing import Any
from rich.console import Console
from enum import Enum
from emu import ins_codes


version_string = "v0.0.1"


# Define the instructions and their corresponding opcodes
INSTRUCTIONS = {
    "nop": {"opcode": 0x00, "args": 0},
    "int": {"opcode": 0x01, "args": 1},
    "hlt": {"opcode": 0x02, "args": 0},
    "mov": {"opcode": 0x03, "args": 3},
    "jne": {"opcode": 0x04, "args": 2},
    "je": {"opcode": 0x05, "args": 2},
    "jnz": {"opcode": 0x06, "args": 2},
    "jz": {"opcode": 0x07, "args": 2},
    "add": {"opcode": 0x08, "args": 2},
    "sub": {"opcode": 0x09, "args": 2},
    "mul": {"opcode": 0x0A, "args": 2},
    "div": {"opcode": 0x0B, "args": 2},
    "jmp": {"opcode": 0x0C, "args": 1},
    "inb": {"opcode": 0x0D, "args": 1},
    "outb": {"opcode": 0x0E, "args": 1},
    "and": {"opcode": 0x0F, "args": 2},
    "or": {"opcode": 0x10, "args": 2},
    "cmp": {"opcode": 0x11, "args": 2},
    "nor": {"opcode": 0x12, "args": 2},
    "inc": {"opcode": 0x13, "args": 1},
    "dec": {"opcode": 0x14, "args": 1},
    "uld": {"opcode": 0x15, "args": 0}
}

# Define the data and text headers and their corresponding characters
HEADERS = {
    "data": chr(0x10FFFF),
    "text": chr(0x10FFFD)
}

# Define the label dictionary to store label addresses
LABELS = {}

# Define the register table used for parsing later
REGISTERS = {
    "eax": chr(0x10FF8),
    "ebx": chr(0x10FF9),
    "ecx": chr(0x10FFA),
    "edx": chr(0x10FFB),
    "ax": chr(0x10FC),
    "bx": chr(0x10FD),
    "cx": chr(0x10FE),
    "dx": chr(0x10FF),
    "bax": chr(0x11000),
    "bbx": chr(0x11001),
    "bcx": chr(0x11002),
    "bdx": chr(0x11003),
    "rs": chr(0x11004)
}

console = Console()


class TokenType(Enum):
    Instruction = 1
    String = 2
    Number = 3
    Header = 4
    Label = 5
    Register = 6
    Comment = 7


def parse_tokens(tokens: list[dict[str, Any]], output_file: str):
    # Handle errors
    assert type(tokens) == list, "Type of `tokens` is not list"
    assert type(output_file) == str, "Type of `output_file` is not str"

    if os.path.isfile(output_file):
        file = open(output_file, "w", encoding="utf-16")
    else:
        file = open(output_file, "a", encoding="utf-16")

    output_buffer = ""

    pos = 0

    while pos < len(tokens):
        tok = tokens[pos]

        if tok["type"] == TokenType.Header:
            output_buffer += HEADERS[tok["value"]]
        elif tok["type"] == TokenType.Comment:
            pos += 1
            continue
        elif tok["type"] == TokenType.Label:
            pos += 1

            if tokens[pos]["type"] == TokenType.String:
                string = tokens[pos]["value"].replace("\\n", "\n")

                for char in string:
                    output_buffer += char
            else:
                return f"Cannot have label with specified type at token \"{tokens[pos]['value']}\""
        elif tok["type"] == TokenType.Instruction:
            try:
                test = INSTRUCTIONS[tok["value"]]
            except KeyError:
                return f"Invalid instruction \"{tok['value']}\""

            if tok["value"] == INSTRUCTIONS["nop"]:
                continue # Nop instruction, reduce file size by ignoring them
            
            output_buffer += chr(INSTRUCTIONS[tok["value"]]["opcode"])
            
            for i in range(INSTRUCTIONS[tok["value"]]["args"]):
                pos += 1
                if pos >= len(tokens):
                    return f"Invalid number of arguments for {tok['value']} instruction"

                if tokens[pos]["type"] == TokenType.Number:
                    output_buffer += chr(tokens[pos]["value"])
                elif tokens[pos]["type"] == TokenType.Register:
                    if REGISTERS.get(tokens[pos]["value"]):
                        output_buffer += REGISTERS[tokens[pos]["value"]]
        else:
            return f"Expected instruction, header, or label at token \"{tokens[pos]['value']}\""

        pos += 1

    file.write(output_buffer)
    file.close()

    return None


# Tokenize an input buffer so that it can be parsed later
def tokenize(buffer: str):
    # Handle errors
    assert type(buffer) == str, "Type of `buffer` is not str"

    pos = 0
    column = 1
    row = 0

    length = len(buffer)

    error = None
    tokens = []

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    numbers = "1234567890"

    while pos < length:
        current_character = buffer[pos]

        if current_character == " " or current_character == "/t":
            column += 1
            pos += 1
            continue
        elif current_character == "\n":
            column = 1
            row += 1
            pos += 1
            continue
        elif current_character == "\"":
            res = ""

            pos += 1
            column += 1

            while pos < length and buffer[pos] != "\"":
                res += buffer[pos]
                pos += 1
                column += 1

            tokens.append({"type": TokenType.String, "value": res})
        elif current_character == "\'":
            res = ""
            
            pos += 1
            column += 1

            while pos < length and buffer[pos] != "\'":
                res += buffer[pos]
                pos += 1
                column += 1

            tokens.append({"type": TokenType.String, "value": res})
        elif current_character == "*":
            res = ""

            while pos < length and buffer[pos] != "\n":
                res += buffer[pos]
                pos += 1
                column += 1

            tokens.append({"type": TokenType.Comment, "value": res})
        elif current_character == ".":
            res = ""

            pos += 1

            while pos < length and buffer[pos] in chars:
                res += buffer[pos]
                pos += 1
                column += 1
            
            if HEADERS.get(res):
                tokens.append({"type": TokenType.Header, "value": res})
            else:
                error = f"Invalid header at line {row}, column {column}"
                break
        elif current_character == ",":
            pos += 1
            column += 1
            continue
        elif current_character in chars:
            res = ""

            while pos < length and (buffer[pos] in chars or buffer[pos] == ":"):
                res += buffer[pos]
                pos += 1
                column += 1
            
            if INSTRUCTIONS.get(res):
                tokens.append({"type": TokenType.Instruction, "value": res})
            else:
                if res.endswith(":"):
                    tokens.append({"type": TokenType.Label, "value": res})
                else:
                    if REGISTERS.get(res.lower()):
                        tokens.append({"type": TokenType.Register, "value": res})
                    else:
                        error = f"Invalid syntax at line {row}, column {column}"
                        break
        elif current_character in numbers:
            res = ""

            is_hex = False

            while pos < length and (buffer[pos] in numbers or buffer[pos] in chars or buffer[pos] == "x"):
                res += buffer[pos]
                pos += 1
                column += 1

            try:
                res.index("x")
                is_hex = not is_hex
            except ValueError:
                is_hex = False

            try:
                tokens.append({"type": TokenType.Number, "value": int(res.lower(), 0)})
            except ValueError:
                error = f"Malformed number \"{res}\" at line {row}, column {column}"
                break
        else:
            error = f"Unrecognized token \"{current_character}\" at line {row}, column {column}"
            break

        pos += 1

    return tokens, error

# Function to assemble the input file
def assemble(buffer: str, output_file: str):
    # Handle errors
    assert type(buffer) == str, "Type of `buffer` is not str"
    assert type(output_file) == str, "Type of `output_file` is not str"

    tokens, error = tokenize(buffer)
    if error:
        console.print(f"[bold red]error: {error}[/bold red]")
        return
    
    error = parse_tokens(tokens, output_file)
    if error:
        console.print(f"[bold red]error: {error}[/bold red]")
        return
    
    console.print("[bold green]Assembled successfully.[/bold green]")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="SPK-8 Assembler",
        description="The assembler for the SPK-8.",
        epilog="This assembler is in BETA! Do not use it for production purposes."
    )

    positional_args = parser.add_argument_group("positional arguments")
    positional_args.add_argument("--file", "-f", help="The source file.")
    positional_args.add_argument("--output", "-o", help="The output file's name.", default="output.mem")

    optional_args = parser.add_argument_group("optional arguments")
    optional_args.add_argument("--verbose", "-v", help="Print more information in a verbose format.", action="store_true")
    optional_args.add_argument("--version", "-V", help="Print version and exit.", action="store_true")

    args = parser.parse_args()

    if args.version: # Show version and exit
        console.print("[bold bright_green]SPK-8 Assembler[/bold bright_green]")
        console.print(f"[dim white]{version_string}[/dim white]")
        sys.exit()

    if not args.file: # The input file was not given
        console.print("[bold red]fatal: no input file[/bold red]")
        sys.exit()

    try:
        # Read the input file
        f = open(args.file, "r", encoding="utf-8")
        buffer = f.read()
    except FileNotFoundError:
        # The input file doesn't exist
        console.print("[bold red]fatal: input file doesn't exist[/bold red]")
        sys.exit()
    except Exception as e:
        # Any other FS related error
        console.print(f"[bold red]fatal: {e}[/bold red]")
        sys.exit()
    
    assemble(buffer, args.output)

    f.close() # No memory leaks!


if __name__ == "__main__":
    main()