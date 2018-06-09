import os
import pygame
import random
import sys
import time
import tkinter as tk
from tkinter import filedialog


class Chip8:
    memory = [0] * 4096
    V = [0] * 16  # Registers
    I = 0
    pc = 0x200
    gfx = [[0] * 64 for i in range(32)]
    delay_timer = 0
    sound_timer = 0
    stack = [0] * 16
    sp = 0
    key = [0] * 16

    font = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80]  # F

    def __init__(self, romname):
        for i in range(80):
            self.memory[i] = self.font[i]
        with open(romname, 'rb') as rom:
            for i in range(os.path.getsize(romname)):
                try:
                    self.memory[512 + i] = ord(rom.read(1))  # Write ROM to the memory
                except IndexError:
                    raise Exception('Invalid ROM!')

    def Cycle(self):
        try:
            opcode = (self.memory[self.pc] << 8 | self.memory[self.pc + 1])
        except IndexError:
            raise Exception('Invalid ROM!')

        self.ExecInstr(opcode)
        if(self.delay_timer > 0):
            self.delay_timer -= 1
        if(self.sound_timer > 0):
            self.sound_timer -= 1

    def ExecInstr(self, opcode):
        first = opcode >> 12
        last = opcode & 0xF
        last2 = opcode & 0xFF
        last3 = opcode & 0xFFF

        VX = (opcode & 0xF00) >> 8
        VY = (opcode & 0xF0) >> 4

        for i in range(16):
            self.V[i] = int(self.V[i])

        if(first == 0x0):
            if(last3 == 0x0E0):
                self.gfx = [[0] * 64 for i in range(36)]
            elif(last3 == 0x0EE):
                self.sp -= 1
                self.pc = self.stack[self.sp]
            self.pc += 2
            # 0NNN is not important
        elif(first == 0x1):
            self.pc = last3
        elif(first == 0x2):
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = last3
        elif(first == 0x3):
            if(self.V[VX] == last2):
                self.pc += 4
            else:
                self.pc += 2
        elif(first == 0x4):
            if(self.V[VX] != last2):
                self.pc += 4
            else:
                self.pc += 2
        elif(first == 0x5):
            if(self.V[VX] == self.V[VY]):
                self.pc += 4
            else:
                self.pc += 2
        elif(first == 0x6):
            self.V[VX] = last2
            self.pc += 2
        elif(first == 0x7):
            self.V[VX] = (self.V[VX] + last2)
            self.pc += 2
        elif(first == 0x8):
            if(last == 0x0):
                self.V[VX] = self.V[VY]
            elif(last == 0x1):
                self.V[VX] = (self.V[VX] | self.V[VY])
            elif(last == 0x2):
                self.V[VX] = (self.V[VX] & self.V[VY])
            elif(last == 0x3):
                self.V[VX] = (self.V[VX] ^ self.V[VY])
            elif(last == 0x4):
                self.V[VX] = (self.V[VX] + self.V[VY])
                if(self.V[VX] > 0xFF):
                    self.V[0xF] = True
                    self.V[VX] = (self.V[VX] & 0xFF)
                else:
                    self.V[0xF] = False
            elif(last == 0x5):
                if(self.V[VX] > self.V[VY]):
                    self.V[0xF] = True
                else:
                    self.V[0xF] = False
                self.V[VX] = (self.V[VX] - self.V[VY])
            elif(last == 0x6):
                self.V[0xF] = (self.V[VX] & 0b1)
                self.V[VX] /= 2
            elif(last == 0x7):
                if(self.V[VY] > self.V[VX]):
                    self.V[0xF] = True
                else:
                    self.V[0xF] = False
                self.V[VX] = (self.V[VY] - self.V[VX])
            elif(last == 0xE):
                self.V[0xF] = (self.V[VX] >> 7)
                self.V[VX] *= 2
            self.pc += 2
        elif(first == 0x9):
            if(self.V[VX] != self.V[VY]):
                self.pc += 4
            else:
                self.pc += 2
        elif(first == 0xA):
            self.I = last3
            self.pc += 2
        elif(first == 0xB):
            self.pc = (last3 + self.V[0x0])
        elif(first == 0xC):
            self.V[VX] = (random.randrange(0, 255) & last2)
            self.pc += 2
        elif(first == 0xD):  # Draw
            x = self.V[VX]
            y = self.V[VY]
            self.V[0XF] = False
            for line in range(last):
                pixels = self.memory[self.I + line]
                for column in range(8):
                    final_y = ((y + line) % 32)
                    final_x = ((x + column) % 64)
                    if((pixels & (0b10000000 >> column)) != 0):
                        if(self.gfx[final_y][final_x] == 1):
                            self.V[0xF] = True
                        self.gfx[final_y][final_x] ^= 1
            self.pc += 2
        elif(first == 0xE):
            if(last2 == 0x9E):
                if(self.key[self.V[VX]]):
                    self.pc += 4
                else:
                    self.pc += 2
            if(last2 == 0xA1):
                if(not self.key[self.V[VX]]):
                    self.pc += 4
                else:
                    self.pc += 2
        elif(first == 0xF):
            if(last2 == 0x07):
                self.V[VX] = self.delay_timer
            elif(last2 == 0x0A):
                pressed = False
                for i in range(16):
                    if(self.key[i]):
                        pressed = True
                        self.V[VX] = i
                if(not pressed):
                    return
            elif(last2 == 0x15):
                self.delay_timer = self.V[VX]
            elif(last2 == 0x18):
                self.sound_timer = self.V[VX]
            elif(last2 == 0x1E):
                self.I += self.V[VX]
                if(self.I > 0xFFF):  # Maybe FFFF
                    self.V[0xF] = True
                else:
                    self.V[0xF] = False
            elif(last2 == 0x29):
                self.I = (self.V[VX] * 0x5)
            elif(last2 == 0x33):
                self.memory[self.I] = int(self.V[VX] / 100)
                self.memory[self.I + 1] = int((self.V[VX] % 100) / 10)
                self.memory[self.I + 2] = int(self.V[VX] % 10)
            elif(last2 == 0x55):
                for i in range(VX + 1):
                    self.memory[self.I + i] = self.V[i]
            elif(last2 == 0x65):
                for i in range(VX + 1):
                    self.V[i] = self.memory[self.I + i]
            self.pc += 2


def Main():
    root = tk.Tk()
    root.withdraw()

    romname = filedialog.askopenfilename()
    sys8 = Chip8(romname)

    pygame.display.set_icon(pygame.image.load('icon.bmp'))
    pygame.display.set_caption('PYHC-8')
    native_display = pygame.Surface((64, 32))
    display_array = pygame.PixelArray(native_display)
    pc_display = pygame.display.set_mode((640, 320))

    while True:
        """ prev_time = time.time() """

        pygame.event.pump()
        pressed = pygame.key.get_pressed()

        sys8.key[0x0] = pressed[pygame.K_x]
        sys8.key[0x1] = pressed[pygame.K_1]
        sys8.key[0x2] = pressed[pygame.K_2]
        sys8.key[0x3] = pressed[pygame.K_3]
        sys8.key[0x4] = pressed[pygame.K_q]
        sys8.key[0x5] = pressed[pygame.K_w]
        sys8.key[0x6] = pressed[pygame.K_e]
        sys8.key[0x7] = pressed[pygame.K_a]
        sys8.key[0x8] = pressed[pygame.K_s]
        sys8.key[0x9] = pressed[pygame.K_d]
        sys8.key[0xa] = pressed[pygame.K_z]
        sys8.key[0xb] = pressed[pygame.K_c]
        sys8.key[0xc] = pressed[pygame.K_4]
        sys8.key[0xd] = pressed[pygame.K_r]
        sys8.key[0xe] = pressed[pygame.K_f]
        sys8.key[0xf] = pressed[pygame.K_v]

        time.sleep(0.00125)  # This is bad
        sys8.Cycle()

        for i in range(32):
            for j in range(64):
                if(sys8.gfx[i][j]):
                    display_array[j][i] = 0xFFFFFF
                else:
                    display_array[j][i] = 0x0
        pygame.transform.scale(native_display, (640, 320), pc_display)
        pygame.display.update()

        if(pressed[pygame.K_ESCAPE]):
            sys.exit()

        """ curr_time = time.time()  # Fix this sometime
        if((curr_time - prev_time) < 0.0166666666666667):
            time.sleep(0.0166666666666667 - (curr_time - prev_time))
            print(0.0166666666666667 - (curr_time - prev_time)) """


if __name__ == "__main__":
    Main()
