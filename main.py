import ctypes
import hashlib
import os
import pickle
import random
import sys
import subprocess
import time

try:
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    import PyQt5.QtWidgets as QtWidgets
except:
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'PyQt5'])
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    import PyQt5.QtWidgets as QtWidgets

if(sys.version.startswith('3.7')):
    print('Please use Python 3.6.x, as 3.7 is broken with the keyboard module.')
    sys.exit(1)

try:
    import keyboard
except:
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'keyboard'])
    import keyboard

DEBUG = False
CLOCK = 300  # Hz, multiples of 60: 60, 120, ..., 600 are the recommended values
REFRESH = 60  # Hz
CYCLES_PER_FRAME = int(CLOCK / REFRESH)

def DebugPrint(text):
    if(DEBUG):
        print(text)

class Chip8:
    memory = [0] * 4096
    V = [0] * 16
    I = 0
    pc = 0x200
    gfx = [[0] * 64 for i in range(32)]
    delay_timer = 0
    sound_timer = 0
    stack = [0] * 16
    sp = 0

    locked = True

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

    keymap = {0: 'x', 1: '1', 2: '2', 3: '3',
              4: 'q', 5: 'w', 6: 'e', 7: 'a',
              8: 's', 9: 'd', 10: 'z', 11: 'c',
              12: '4', 13: 'r', 14: 'f', 15: 'v'}

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

    def ExecInstr(self, opcode):
        first = opcode >> 12
        last = opcode & 0xF
        last2 = opcode & 0xFF
        last3 = opcode & 0xFFF

        VX = (opcode & 0xF00) >> 8
        VY = (opcode & 0xF0) >> 4

        for i in range(16):
            if(not isinstance(self.V[i], int)):
                DebugPrint(f'Invalid value: V[{i}] = {self.V[i]}')
                self.V[i] = int(self.V[i])
            if(self.V[i] > 255):  # Catch all unexpected overflows
                DebugPrint(f'Register overflow: V[{i}] = {self.V[i]}')
                self.V[i] -= 256

        if(first == 0x0):
            if(last3 == 0x0E0):  # Clear the screen
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
            if(self.V[VX] > 255):
                DebugPrint(f'Overflow in 7xxx, V[{VX}] = {self.V[VX]}')
                self.V[VX] -= 256
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
                self.V[VX] = self.V[VX] >> 1
            elif(last == 0x7):
                if(self.V[VY] > self.V[VX]):
                    self.V[0xF] = True
                else:
                    self.V[0xF] = False
                self.V[VX] = (self.V[VY] - self.V[VX])
            elif(last == 0xE):
                self.V[0xF] = (self.V[VX] >> 7)
                self.V[VX] = self.V[VX] << 1
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
            for height in range(last):
                final_y = ((y + height) % 32)
                pixels = self.memory[self.I + height]
                for width in range(8):
                    final_x = ((x + width) % 64)
                    if((pixels & (0b10000000 >> width)) != 0):
                        if(self.gfx[final_y][final_x] == 1):
                            self.V[0xF] = True
                        self.gfx[final_y][final_x] ^= 1
            self.pc += 2
        elif(first == 0xE):  # Slowest part of the code, the keyboard module is not really efficient
            yz_pressed = False
            if(self.V[VX] == 10):  # Try to minimise the usage of the slow keyboard
                yz_pressed = keyboard.is_pressed('z')
            if(last2 == 0x9E):
                if(keyboard.is_pressed(self.keymap[self.V[VX]]) or yz_pressed):  # Support more keyboard layouts
                    self.pc += 4
                else:
                    self.pc += 2
            if(last2 == 0xA1):
                if not (keyboard.is_pressed(self.keymap[self.V[VX]]) or yz_pressed):
                    self.pc += 4
                else:
                    self.pc += 2
        elif(first == 0xF):
            if(last2 == 0x07):
                self.V[VX] = self.delay_timer
            elif(last2 == 0x0A):
                while(self.locked):
                    time.sleep(0.000001)
                self.V[VX] = self.keypress
                self.locked = True
            elif(last2 == 0x15):
                self.delay_timer = self.V[VX]
            elif(last2 == 0x18):
                self.sound_timer = self.V[VX]
            elif(last2 == 0x1E):
                self.I += self.V[VX]
                if(self.I > 0xFFF):
                    self.V[0xF] = True
                else:
                    self.V[0xF] = False
            elif(last2 == 0x29):
                self.I = (0x0 + self.V[VX] * 0x5)  # 0x0 is the font adress
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

    def SaveState(self):
        ui.core.locked = True
        romhash = Util.HashRom(ui.core.romname)
        V = self.V
        I = self.I
        pc = self.pc
        gfx = self.gfx
        delay_timer = self.delay_timer
        sound_timer = self.sound_timer
        stack = self.stack
        sp = self.sp
        data = [romhash, V, I, pc, gfx, delay_timer,
                sound_timer, stack, sp]
        with open('SaveState', 'wb') as statefile:
            pickle.dump(data, statefile)
        ui.core.locked = False

    def LoadState(self):
        ui.core.locked = True
        romhash = Util.HashRom(ui.core.romname)
        with open('SaveState', 'rb') as statefile:
            data = pickle.load(statefile)
            if(romhash != data[0]):
                ctypes.windll.user32.MessageBoxW(0, "The savestate that you tried to load is from another game!", "Error", 0)
                ui.core.locked = False
                return
            self.V = data[1]
            self.I = data[2]
            self.pc = data[3]
            self.gfx = data[4]
            self.delay_timer = data[5]
            self.sound_timer = data[6]
            self.stack = data[7]
            self.sp = data[8]
        ui.core.locked = False

    def KeyAction(self, event):
        if(event.name == 'f1'):
            self.LoadState()

        elif(event.name == 'f3'):
            self.SaveState()

        else:
            if(event.name == 'x'): self.keypress = 0
            if(event.name == '1'): self.keypress = 1
            if(event.name == '2'): self.keypress = 2
            if(event.name == '3'): self.keypress = 3
            if(event.name == 'q'): self.keypress = 4
            if(event.name == 'w'): self.keypress = 5
            if(event.name == 'e'): self.keypress = 6
            if(event.name == 'a'): self.keypress = 7
            if(event.name == 's'): self.keypress = 8
            if(event.name == 'd'): self.keypress = 9
            if(event.name == 'z'): self.keypress = 10
            if(event.name == 'y'): self.keypress = 10  # Some keyboard layouts have Z and Y mixed
            if(event.name == 'c'): self.keypress = 11
            if(event.name == '4'): self.keypress = 12
            if(event.name == 'r'): self.keypress = 13
            if(event.name == 'f'): self.keypress = 14
            if(event.name == 'v'): self.keypress = 15
            self.locked = False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.InitUI()

    def InitUI(self):
        self.core = EmuCore()
        self.emu_thread = QtCore.QThread()
        self.core.moveToThread(self.emu_thread)

        self.open_act = QtWidgets.QAction('Open ROM', self)
        self.open_act.triggered.connect(Util.Launch)

        exit_act = QtWidgets.QAction('Exit', self)
        exit_act.triggered.connect(self.emu_thread.quit)
        exit_act.triggered.connect(QtWidgets.qApp.quit)

        """ self.save_act = QtWidgets.QAction('Save state', self)
        self.save_act.triggered.connect(self.core.sys8.SaveState)
        self.save_act.setEnabled(False)

        self.load_act = QtWidgets.QAction('Load state', self)
        self.load_act.triggered.connect(self.core.sys8.LoadState)
        self.load_act.setEnabled(False) """

        menubar = self.menuBar()
        filemenu = menubar.addMenu('File')
        filemenu.addAction(self.open_act)
        filemenu.addAction(exit_act)
        """ emumenu = menubar.addMenu('Emulation')
        emumenu.addAction(self.save_act)
        emumenu.addAction(self.load_act) """

        self.native = QtGui.QBitmap(64, 32)
        self.native.fill(QtCore.Qt.color1)
        self.scaled = QtWidgets.QLabel(self)
        self.scaled.setPixmap(self.native.scaled(1280, 640, QtCore.Qt.KeepAspectRatio))
        self.setCentralWidget(self.scaled)

        self.painter = QtGui.QPainter(self.native)
        self.painter.setPen(QtCore.Qt.color0)

        self.setGeometry(320, 210, 1280, 660)  # Improve this later
        self.setWindowTitle('PYHC-8')
        self.setWindowIcon(QtGui.QIcon('icon.bmp'))
        self.show()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    @QtCore.pyqtSlot(list)
    def Draw(self, gfx):
        self.native.fill(QtCore.Qt.color1)
        for i in range(32):
            for j in range(64):
                if(gfx[i][j]):
                    self.painter.drawPoint(j, i)

        self.scaled.setPixmap(ui.native.scaled(1280, 640))
        self.scaled.repaint()
        return


class Util():
    @staticmethod
    def HashRom(romname):
        with open(romname, 'rb') as rom:
            md5 = hashlib.new('md5')
            md5.update(rom.read())
            return(md5.hexdigest())

    @staticmethod
    def Launch():
        filepath = QtWidgets.QFileDialog.getOpenFileName(None, 'Open ROM', '', 'CHIP-8 ROMS (*.*)')
        if(filepath[0] != ''):
            ui.core.romname = filepath[0]
            ui.emu_thread.started.connect(ui.core.run)
            ui.emu_thread.start()


class EmuCore(QtCore.QObject):
    gfx_upl = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.romname = ''
        self.locked = False

    def run(self):
        self.sys8 = Chip8(self.romname)
        self.romhash = Util.HashRom(self.romname)

        ui.open_act.setEnabled(False)
        """ ui.save_act.setEnabled(True)
        ui.load_act.setEnabled(True) """

        self.gfx_upl.connect(ui.Draw, type = QtCore.Qt.BlockingQueuedConnection)
        keyboard.hook(self.sys8.KeyAction)
        while(True):
            curr_ccl = 0
            while(curr_ccl < CYCLES_PER_FRAME):
                if(not self.locked):
                    self.sys8.Cycle()
                    curr_ccl += 1
            self.gfx_upl.emit(self.sys8.gfx)
            if(self.sys8.delay_timer > 0):
                self.sys8.delay_timer -= 1
            if(self.sys8.sound_timer > 0):
                QtWidgets.QApplication.beep()
                self.sys8.sound_timer -= 1


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    sys.exit(app.exec_())
