#==// REG IMEDIATES \\==#
Addr_RegIm8 = 0x07
Addr_RegIm16 = 0x06

#==// HEADERS \\==#
HEADER_DATA = 0x10FFFF # Varibales
HEADER_ROM  = 0x10FFFE # Constants
HEADER_TEXT = 0x10FFFD # Actual code ( totally didn't copy nasm ;) )

#==// REG CODES \\==#
Code_EAX = 0x10FF8
Code_EBX = 0x10FF9
Code_ECX = 0x10FFA
Code_EDX = 0x10FFB

Code_AX = 0x10FFC
Code_BX = 0x10FFD
Code_CX = 0x10FFE
Code_DX = 0x10FFF

Code_BAX = 0x11000
Code_BBX = 0x11001
Code_BCX = 0x11002
Code_BDX = 0x11003
Code_RS = 0x11004

#==// INSTRUCTIONS \\==#
NOP = 0x00
INT = 0x01
HLT = 0x02
MOV = 0x03
JNE = 0x04
JE = 0x05
JNZ = 0x06
JZ = 0x07
ADD = 0x08
SUB = 0x09
MUL = 0x0A
DIV = 0x0B
JMP = 0x0C
INB = 0x0D
OUTB = 0x0E
AND = 0x0F
OR = 0x10
CMP = 0x11
NOR = 0x12
INC = 0x13
DEC = 0x14
ULD = 0x15