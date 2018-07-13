#import fileinput
#import termios
#import argparse
import os
import sys
import shutil
import tty
import termios
import atexit
from curses.ascii import ctrl

class Jin():
#TODO: block signals, set flags, read text files

    def __init__(self):
        # initialize fields
        self.dimensions = shutil.get_terminal_size() # stored as (columns, lines)
        self.default_attr = termios.tcgetattr(sys.stdin.fileno())
        self.reset_outbuf()
        self.cx = 0
        self.cy = 0

        # enable and disable raw mode
        self.enable_raw()
        atexit.register(self.disable_raw)

        self.editor_clear_screen()
        while(True):
            self.editor_clear_screen()
            self.process_keypress(self.read_keypress())


    def reset_outbuf(self):
        self.outbuf = []

    def append_outbuf(self, output):
        self.outbuf.append(output)

    def write_outbuf(self):
        sys.stdout.write(''.join(self.outbuf))
        self.reset_outbuf()

    def read_keypress(self):
        inp = sys.stdin.read(1)
        return inp

    def decrementy(self):
        if self.cy:
            self.cy -= 1
    def decrementx(self):
        if self.cx:
            self.cx -= 1
    def incrementy(self):
        if self.cy < self.dimensions.lines:
            self.cy += 1
    def incrementx(self):
        if self.cx < self.dimensions.columns:
            self.cx += 1

    def process_keypress(self, key_pressed):
        key_switcher = {
            ctrl('q'): sys.exit,
            'h': self.decrementx,
            'j': self.incrementx,
            'k': self.decrementy,
            'l': self.incrementy,
        }
        if key_pressed in key_switcher:
            key_switcher[key_pressed]()


    def enable_raw(self):
        tty.setraw(sys.stdin.fileno())

    def disable_raw(self):
        # tty.setcbreak(sys.stdin.fileno())
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, self.default_attr)

    def editor_clear_screen(self):
        self.append_outbuf('\x1b[?25l')
        os.system('clear')
        # sys.stdout.write('\x1b[2J')
        self.draw_rows()
        self.append_outbuf('\x1b[{};{}H'.format(self.cy + 1, self.cx + 1))
        self.append_outbuf('\x1b[?25h')
        self.write_outbuf()

    def draw_rows(self):
        for i in range(self.dimensions.lines - 1):
            self.append_outbuf('~')

            if i == self.dimensions.lines // 3:
                welcome_msg = 'Welcome to my text editor!!!!!!!!!!!!!!'
                padding = ' ' * ((self.dimensions.columns - len(welcome_msg)) // 2)
                self.append_outbuf(padding + welcome_msg)

            self.append_outbuf('\r\n') # fills each row with a ~
        self.append_outbuf('~') # last row edgecase
        self.append_outbuf('\x1b[H') # moves cursor back to top left of screen

if __name__ == "__main__":
    jin = Jin()

