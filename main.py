import sys
import pygame
import time
import chip8
import tkinter as tk
from tkinter import filedialog

def Main():
    root = tk.Tk()
    root.withdraw()

    romname = filedialog.askopenfilename()
    sys8 = chip8.Chip8(romname) # Add check for invalid ROM

    native_display = pygame.Surface((64, 32))
    display_array = pygame.PixelArray(native_display)
    pc_display = pygame.display.set_mode((640,320))

    while True:
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

        sys8.Cycle(sys8.key)
        if(sys8.draw_flag == True):
            for i in range(32):
                for j in range(64):
                    if(sys8.gfx[i][j]):
                        display_array[j][i] = 0xFFFFFF
                    else:
                        display_array[j][i] = 0x0
            pygame.transform.scale(native_display, (640, 320), pc_display)
            pygame.display.update()


if __name__ == "__main__":
    Main()