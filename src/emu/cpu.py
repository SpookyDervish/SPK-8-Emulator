from memory import Memory
from typing import Any
from ins_codes import *
from screen import writes, clear, draw_pix, set_colour, reset_scroll
from fs import mkdir, create_file, writef, ls, rm, cd


class Flags:
    def __init__(self):
        self.Z = 0 # ALU returned zero result
        self.C = 0 # ALU returns > 32-bit limit "borrow"
        self.O = 0 # Overflow, carry-in and carry-out are oppisite
        self.S = 0 # Sign, "negative"

        self.B = 0 # Busy
        self.T = 0 # Single-step, trap flag
        self.I = 0 # Interrupts disabled
        self.E = 0 # There is an interrupt
        self.R = 0 # Restart

    def full(self):
        """Combine all flags into a single byte
        """
        ps = self.Z << 7 | self.C << 6 | self.O << 5 | self.S << 4 | self.B << 3 | self.T << 2 | self.I << 1 | self.E
        return ps

class CPU:

    Syscall = 0x80
    COM0 = 0xF001
    IntLoc = 0xF000
    VarLoc = 0xFF00

    Reserved =            0x00
    SingleStepInterrupt = 0x01
    Breakpoint          = 0x03
    InvalidOpcode =       0x06
    DoubleFault =         0x08
    OutOfMemory =         0x16

    Sys_RestartSyscall =  0x00

    Sys_Exit = 0x01
    Sys_Fork = 0x02
    Sys_Read = 0x03
    Sys_Write = 0x04
    Sys_Open = 0x05
    Sys_Close = 0x06
    Sys_Create = 0x08
    Sys_Time = 0x0D
    Sys_fTime = 0x23

    def __init__(self, screen):
        self.PC = 0 # Program counter
        self.PS = Flags()

        # Registers
        self.EAX = 0 # Extended (32-bit), A, X (General Purpose)
        self.EBX = 0
        self.ECX = 0
        self.EDX = 0

        self.EDI = 0 # Destination index
        self.ESI = 0 # Source index
        self.ESP = 0 # Stack pointer
        self.EBP = 0 # Address offset

        self.AX = 0 # 16-bits
        self.BX = 0
        self.CX = 0
        self.DX = 0
        self.BAX = 0 # B (8-bit), A, X (General Purpose)
        self.BBX = 0
        self.BCX = 0
        self.BDX = 0

        self.RS = 0 # Result register

        self.memory = Memory().data
        self.buffer = len(self.memory)
        self.original_memory = Memory()
        self.debug = False
        self.in_interrupt = False
        self.screen = screen

    def LoadMemory(self, memory: Memory):
        self.memory = memory.data
        self.buffer = len(self.memory)
        self.original_memory = memory

    def __FetchByte(self) -> int:
        value = self.memory[self.PC]
        self.PC += 1

        return value
    
    def __FetchWord(self) -> int:
        return self.__FetchByte() << 8 | self.__FetchByte()
    
    def __WriteReg(self, code: int, value: int) -> None:
        if code == Code_EAX:
            self.EAX = value

        elif code == Code_EBX:
            self.EBX = value

        elif code == Code_ECX:
            self.ECX = value

        elif code == Code_EDX:
            self.EDX = value

        elif code == Code_AX:
            self.AX = value

        elif code == Code_BX:
            self.BX = value

        elif code == Code_CX:
            self.CX = value

        elif code == Code_DX:
            self.DX = value

        elif code == Code_BAX:
            self.BAX = value

        elif code == Code_BBX:
            self.BBX = value

        elif code == Code_BCX:
            self.BCX = value

        elif code == Code_BDX:
            self.BDX = value

        elif code == Code_RS:
            self.RS = value

    def __IsReg(self, code: int):
        if code == Code_EAX:
            return [True, self.EAX]
        elif code == Code_EBX:
            return [True, self.EBX]
        elif code == Code_ECX:
            return [True, self.ECX]
        elif code == Code_EDX:
            return [True, self.EDX]
        elif code == Code_AX:
            return [True, self.AX]
        elif code == Code_BX:
            return [True, self.BX]
        elif code == Code_CX:
            return [True, self.CX]
        elif code == Code_DX:
            return [True, self.DX]
        elif code == Code_BAX:
            return [True, self.BAX]
        elif code == Code_BBX:
            return [True, self.BBX]
        elif code == Code_BCX:
            return [True, self.BCX]
        elif code == Code_BDX:
            return [True, self.BDX]
        elif code == Code_RS:
            return [True, self.RS]
        return [False, 0]

    def __RaiseInterrupt(self, code: int, **kwargs) -> None:
        try:
            string = "CPU: Interrupt: "

            if code == self.InvalidOpcode:
                if 'opcode' in kwargs:
                    string += "InvalidOpcode: %s at address %s" % (hex(kwargs['opcode']), hex(self.PC))
                else:
                    string += "InvalidOpcode: Unkown at address %s" % hex(self.PC)
                
            elif code == self.OutOfMemory:
                string += "OutOfMemory: %s" % hex(self.PC)

            elif code == self.SingleStepInterrupt:
                string += "SingleStepInterrupt: %s" % hex(self.PC)
                input(string)
                return
            
            elif code == self.Breakpoint:
                string += "Breakpoint: %s" % hex(self.PC-1)
                input(string)
                return

        except Exception as e:
            if self.debug:
                print("CPU: Interrupt: DoubleFault: Origin: %s" % e)

            raise Exception(string + "DoubleFault: %s" % hex(self.PC))
        
        raise Exception(string)
    
    def __HandleSyscall(self):
        if self.EAX == self.Sys_Write:
            if self.EBX == 1: # Draw text at cursor pos
                string = ''
                counter = 0

                while counter < self.EDX:
                    char = self.memory[self.VarLoc + counter]
                    string += chr(char)
                    counter += 1
                if self.debug:
                    print("CPU: Interrupt: Syscall: Write: Stdout: %s" % string)
                writes(self.screen, string)
            elif self.EBX == 2: # Clear screen
                if self.EDX == 0x0:
                    clear(self.screen, "black")
                elif self.EDX == 0x1:
                    clear(self.screen, "blue3")
                elif self.EDX == 0x2:
                    clear(self.screen, "green3")
                elif self.EDX == 0x3:
                    clear(self.screen, "cyan3")
                elif self.EDX == 0x4:
                    clear(self.screen, "red3")
                elif self.EDX == 0x5:
                    clear(self.screen, "magenta3")
                elif self.EDX == 0x6:
                    clear(self.screen, "brown3")
                elif self.EDX == 0x7:
                    clear(self.screen, "gray")
                elif self.EDX == 0x8:
                    clear(self.screen, "gray3")
                elif self.EDX == 0x9:
                    clear(self.screen, "blue")
                elif self.EDX == 0xA:
                    clear(self.screen, "green")
                elif self.EDX == 0xB:
                    clear(self.screen, "cyan")
                elif self.EDX == 0xC:
                    clear(self.screen, "red")
                elif self.EDX == 0xD:
                    clear(self.screen, "magenta")
                elif self.EDX == 0xE:
                    clear(self.screen, "yellow")
                elif self.EDX == 0xF:
                    clear(self.screen, "white")

                if self.debug:
                    print(f"CPU: Interrupt: Syscall: Write: Clear: {hex(self.EDX)}")
            elif self.EBX == 3: # Draw graphics pixel
                if self.EDX == 0x0:
                    draw_pix(self.screen, (self.AX, self.BX), "black")
                elif self.EDX == 0x1:
                    draw_pix(self.screen, (self.AX, self.BX), "blue3")
                elif self.EDX == 0x2:
                    draw_pix(self.screen, (self.AX, self.BX), "green3")
                elif self.EDX == 0x3:
                    draw_pix(self.screen, (self.AX, self.BX), "cyan3")
                elif self.EDX == 0x4:
                    draw_pix(self.screen, (self.AX, self.BX), "red3")
                elif self.EDX == 0x5:
                    draw_pix(self.screen, (self.AX, self.BX), "magenta3")
                elif self.EDX == 0x6:
                    draw_pix(self.screen, (self.AX, self.BX), "brown3")
                elif self.EDX == 0x7:
                    draw_pix(self.screen, (self.AX, self.BX), "gray")
                elif self.EDX == 0x8:
                    draw_pix(self.screen, (self.AX, self.BX), "gray3")
                elif self.EDX == 0x9:
                    draw_pix(self.screen, (self.AX, self.BX), "blue")
                elif self.EDX == 0xA:
                    draw_pix(self.screen, (self.AX, self.BX), "green")
                elif self.EDX == 0xB:
                    draw_pix(self.screen, (self.AX, self.BX), "cyan")
                elif self.EDX == 0xC:
                    draw_pix(self.screen, (self.AX, self.BX), "red")
                elif self.EDX == 0xD:
                    draw_pix(self.screen, (self.AX, self.BX), "magenta")
                elif self.EDX == 0xE:
                    draw_pix(self.screen, (self.AX, self.BX), "yellow")
                elif self.EDX == 0xF:
                    draw_pix(self.screen, (self.AX, self.BX), "white")

                if self.debug:
                    print(f"CPU: Interrupt: Syscall: Write: DrawPixel: {hex(self.EDX)}")
            elif self.EBX == 4: # Set current text colour
                if self.EDX == 0x0:
                    set_colour("black")
                elif self.EDX == 0x1:
                    set_colour("blue3")
                elif self.EDX == 0x2:
                    set_colour("green3")
                elif self.EDX == 0x3:
                    set_colour("cyan3")
                elif self.EDX == 0x4:
                    set_colour("red3")
                elif self.EDX == 0x5:
                    set_colour("magenta3")
                elif self.EDX == 0x6:
                    set_colour("brown3")
                elif self.EDX == 0x7:
                    set_colour("gray")
                elif self.EDX == 0x8:
                    set_colour("gray3")
                elif self.EDX == 0x9:
                    set_colour("blue")
                elif self.EDX == 0xA:
                    set_colour("green")
                elif self.EDX == 0xB:
                    set_colour("cyan")
                elif self.EDX == 0xC:
                    set_colour("red")
                elif self.EDX == 0xD:
                    set_colour("magenta")
                elif self.EDX == 0xE:
                    set_colour("yellow")
                elif self.EDX == 0xF:
                    set_colour("white")
        elif self.EAX == self.Sys_RestartSyscall: # Restart cpu
            if self.debug:
                print("CPU: Interrupt: Syscall: Restart")
            self.R = True
            self.LoadMemory(self.original_memory)

            self.PC = 0 # Program counter

            # Registers
            self.EAX = 0 # Extended (32-bit), A, X (General Purpose)
            self.EBX = 0
            self.ECX = 0
            self.EDX = 0

            self.EDI = 0 # Destination index
            self.ESI = 0 # Source index
            self.ESP = 0 # Stack pointer
            self.EBP = 0 # Address offset

            self.AX = 0 # 16-bits
            self.BX = 0
            self.CX = 0
            self.DX = 0
            self.BAX = 0 # B (8-bit), A, X (General Purpose)
            self.BBX = 0
            self.BCX = 0
            self.BDX = 0

            self.RS = 0 # Result register
            clear(self.screen)
            set_colour()
            reset_scroll()

    def __HandleInterrupt(self) -> None:
        if self.memory[self.IntLoc] == self.Syscall:
            self.__HandleSyscall()
        else:
            self.__RaiseInterrupt(self.memory[self.IntLoc])

        self.in_interrupt = True
        self.PS.E = 0
    
    def Execute(self) -> Any:
        current_header = "text"
        data_index = 0

        while self.PC < len(self.memory):
            if self.PS.T:
                self.__RaiseInterrupt(self.SingleStepInterrupt)

            if self.PS.R:
                self.PS.R = False
                self.PS = Flags()
                break

            ins = self.__FetchByte()
            var_data_len = self.VarLoc + data_index

            if ins == HEADER_DATA:
                current_header = "data"
                continue
            elif ins == HEADER_ROM:
                current_header = "rom"
                continue
            elif ins == HEADER_TEXT:
                current_header = "text"
                continue
            
            if current_header == "text":
                if ins == HEADER_DATA or ins == HEADER_ROM or ins == HEADER_TEXT:
                    continue # Skip headers

                if ins == NOP:
                    pass # Do nothing lmao

                elif ins == 0xCC:
                    self.__RaiseInterrupt(self.Breakpoint)

                elif ins == MOV:
                    mode = self.__FetchByte()

                    if mode == Addr_RegIm8:
                        reg = self.__FetchByte()
                        value = self.__FetchByte()

                        is_reg = self.__IsReg(value)

                        if is_reg[0] == True:
                            self.__WriteReg(reg, is_reg[1])
                        else:
                            self.__WriteReg(reg, value)
                    elif mode == Addr_RegIm16:
                        reg = self.__FetchByte()
                        value = self.__FetchWord()

                        is_reg = self.__IsReg(value)

                        if is_reg[0] == True:
                            self.__WriteReg(reg, is_reg[1])
                        else:
                            self.__WriteReg(reg, value)

                elif ins == INT:
                    int_code = self.__FetchByte()
                    self.memory[self.IntLoc] = int_code
                    self.__HandleInterrupt()

                elif ins == JMP:
                    value = self.__FetchByte()
                    self.PC = value

                elif ins == ADD:
                    value1 = self.__FetchByte()
                    value2 = self.__FetchByte()

                    is_reg1 = self.__IsReg(value1)
                    is_reg2 = self.__IsReg(value2)

                    number1 = 0
                    number2 = 0

                    if is_reg1[0] == False:
                        number1 = value1
                    elif is_reg1[0] == True:
                        number1 = is_reg1[1]

                    if is_reg2[0] == False:
                        number2 = value2
                    elif is_reg2[0] == True:
                        number2 = is_reg2[1]

                    self.__WriteReg(Code_RS, number1 + number2)

                elif ins == SUB:
                    value1 = self.__FetchByte()
                    value2 = self.__FetchByte()

                    is_reg1 = self.__IsReg(value1)
                    is_reg2 = self.__IsReg(value2)

                    number1 = 0
                    number2 = 0

                    if is_reg1[0] == False:
                        number1 = value1
                    elif is_reg1[0] == True:
                        number1 = is_reg1[1]

                    if is_reg2[0] == False:
                        number2 = value2
                    elif is_reg2[0] == True:
                        number2 = is_reg2[1]

                    self.__WriteReg(Code_RS, number1 - number2)

                elif ins == MUL:
                    value1 = self.__FetchByte()
                    value2 = self.__FetchByte()

                    is_reg1 = self.__IsReg(value1)
                    is_reg2 = self.__IsReg(value2)

                    number1 = 0
                    number2 = 0

                    if is_reg1[0] == False:
                        number1 = value1
                    elif is_reg1[0] == True:
                        number1 = is_reg1[1]

                    if is_reg2[0] == False:
                        number2 = value2
                    elif is_reg2[0] == True:
                        number2 = is_reg2[1]

                    self.__WriteReg(Code_RS, number1 * number2)

                elif ins == DIV:
                    value1 = self.__FetchByte()
                    value2 = self.__FetchByte()

                    is_reg1 = self.__IsReg(value1)
                    is_reg2 = self.__IsReg(value2)

                    number1 = 0
                    number2 = 0

                    if is_reg1[0] == False:
                        number1 = value1
                    elif is_reg1[0] == True:
                        number1 = is_reg1[1]

                    if is_reg2[0] == False:
                        number2 = value2
                    elif is_reg2[0] == True:
                        number2 = is_reg2[1]

                    self.__WriteReg(Code_RS, number1 / number2)

                elif ins == INC:
                    reg = self.__FetchByte()

                    if reg == Code_EAX:
                        self.EAX += 1
                    elif reg == Code_EBX:
                        self.EBX += 1
                    elif reg == Code_ECX:
                        self.ECX += 1
                    elif reg == Code_EDX:
                        self.EDX += 1
                    elif reg == Code_RS:
                        self.RS += 1

                elif ins == DEC:
                    reg = self.__FetchByte()

                    if reg == Code_EAX:
                        self.EAX -= 1
                    elif reg == Code_EBX:
                        self.EBX -= 1
                    elif reg == Code_ECX:
                        self.ECX -= 1
                    elif reg == Code_EDX:
                        self.EDX -= 1
                    elif reg == Code_RS:
                        self.RS -= 1

                elif ins == JNE:
                    value = self.__FetchByte()
                    jmp_loc = self.__FetchByte()

                    if self.RS != value:
                        self.PC = jmp_loc

                elif ins == JE:
                    value = self.__FetchByte()
                    jmp_loc = self.__FetchByte()

                    if self.RS == value:
                        self.PC = jmp_loc

                elif ins == JZ:
                    jmp_loc = self.__FetchByte()

                    if self.RS == 0:
                        self.PC = jmp_loc

                elif ins == JNZ:
                    jmp_loc = self.__FetchByte()

                    if self.RS != 0:
                        self.PC = jmp_loc

                elif ins == AND:
                    value1 = self.__FetchByte()
                    value2 = self.__FetchByte()

                    is_reg1 = self.__IsReg(value1)
                    is_reg2 = self.__IsReg(value2)

                    number1 = 0
                    number2 = 0

                    if is_reg1[0] == False:
                        number1 = value1
                    elif is_reg1[0] == True:
                        number1 = is_reg1[1]

                    if is_reg2[0] == False:
                        number2 = value2
                    elif is_reg2[0] == True:
                        number2 = is_reg2[1]

                    if number1 > 0 and number2 > 0:
                        self.__WriteReg(Code_RS, 1)
                    else:
                        self.__WriteReg(Code_RS, 0)

                elif ins == ULD:
                    for i in range(self.VarLoc, self.VarLoc+data_index):
                        self.memory[i] = 0x0
                    data_index = 0x0

                elif ins == HLT:
                    break # Stop the CPU
                else:
                    # Invalid Opcode                                                                                                                
                    if self.PC - 1 != self.IntLoc and (self.PC - 1 < self.VarLoc or self.PC - 1 > var_data_len):
                        print("InvalidOpcode: %s at address %s" % (hex(ins), hex(self.PC-1)))
            elif current_header == "data":
                if ins == 0x0:                                                                                                              
                    continue
                
                self.memory[self.VarLoc + data_index] = ins
                data_index += 1