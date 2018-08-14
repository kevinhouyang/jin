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
    def __init__(self, file):
        # initialize fields
        self.dimensions = shutil.get_terminal_size() # stored as (columns, lines)
        self.default_attr = termios.tcgetattr(sys.stdin.fileno())
        self.reset_outbuf()
        self.cx, self.cy = 0, 0 # cursor position
        self.erows = [] # number of rows to display
        self.filename = ""
        self.row_offset = 0
        self.col_offset = 0

        if file:
            f = open(file, 'r')
            self.filename = file
            self.erows = f.read().splitlines()

        # enable and disable raw mode
        self.enable_raw()
        atexit.register(self.disable_raw)

        # take in and process input
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

    def decrementy(self):
        if self.cy:
            self.cy -= 1
        elif self.row_offset:
            self.row_offset -= 1

        if self.erows:
            curr_row = self.erows[self.cy + self.row_offset]
            if len(curr_row) < self.cx:
                self.cx = len(curr_row) - 1

    def decrementx(self):
        if self.cx:
            self.cx -= 1
        elif self.col_offset:
            self.col_offset -= 1

    def incrementy(self):
        if self.cy < (self.dimensions.lines - 2) and self.cy < len(self.erows) - 1:
            self.cy += 1
        elif self.cy + self.row_offset < len(self.erows) - 1:
            self.row_offset += 1

        if self.erows:
            curr_row = self.erows[self.cy + self.row_offset]
            if len(curr_row) < self.cx:
                self.cx = len(curr_row) - 1

    def incrementx(self):
        if self.erows:
            curr_row = self.erows[self.cy + self.row_offset]
            if self.cx < self.dimensions.columns and self.cx < len(curr_row) - 1:
                self.cx += 1
            elif self.cx + self.col_offset < len(curr_row) - 1:
                self.col_offset += 1

    def begin_line(self):
        self.cx = 0
        self.col_offset = 0

    def end_line(self):
        curr_row = self.erows[self.cy + self.row_offset]
        if len(curr_row) < self.dimensions.columns:
            self.cx = len(curr_row) - 1
        else:
            self.col_offset = len(curr_row) - self.dimensions.columns
            self.cx = self.dimensions.columns

    def read_keypress(self):
        inp = sys.stdin.read(1)

        if inp == '\x1b':
            inp = sys.stdin.read(2)
            if inp[0] == '[':
                inp_switcher = {
                    'A': 'UP',
                    'B': 'DOWN',
                    'C': 'RIGHT',
                    'D': 'LEFT',
                }
                return inp_switcher[inp[1]]
        return inp

    def process_keypress(self, key_pressed):
        # switch cases for keypresses
        key_switcher = {
            ctrl('q'): sys.exit,
            'h': self.decrementx,
            'j': self.incrementx,
            'k': self.decrementy,
            'l': self.incrementy,
            '0': self.begin_line,
            '$': self.end_line,
            'UP': self.decrementy,
            'DOWN': self.incrementy,
            'RIGHT': self.incrementx,
            'LEFT': self.decrementx,
        }
        if key_pressed in key_switcher:
            key_switcher[key_pressed]()
        else:
            self.editorInsertChar(key_pressed)

    def enable_raw(self):
        tty.setraw(sys.stdin.fileno())

    def disable_raw(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, self.default_attr) # tty.setcbreak(sys.stdin.fileno())

    def editor_clear_screen(self):
        self.append_outbuf('\x1b[?25l') # disappears cursor while rows are being drawn
        os.system('clear') # sys.stdout.write('\x1b[2J')

        self.draw_rows()
        self.draw_status_bar()

        self.append_outbuf('\x1b[{};{}H'.format(self.cy + 1, self.cx + 1)) # repositions cursor
        self.append_outbuf('\x1b[?25h') # reappears cursor
        self.write_outbuf()

    def draw_status_bar(self):
        self.append_outbuf('\x1b[7m')
        status_message = ""
        if self.filename == "":
            status_message = '{} - {} lines'.format("[No Name]", len(self.erows))
        else:
            status_message = '{} - {} lines'.format(self.filename, len(self.erows))
        self.append_outbuf(status_message)

        curr_row_message = "{}/{}".format(self.cy + self.row_offset + 1, len(self.erows))
        self.append_outbuf(" " * (self.dimensions.columns - (len(status_message) + len(curr_row_message))))
        self.append_outbuf(curr_row_message)
        self.append_outbuf('\x1b[m')

    def draw_rows(self):
        for i in range(self.dimensions.lines):
            if i < len(self.erows):
                self.append_outbuf(self.erows[i + self.row_offset - 1][self.col_offset:self.dimensions.columns + self.col_offset])
            else:
                self.append_outbuf('~')
                if i == self.dimensions.lines // 3 and len(self.erows) == 0:
                    welcome_msg = 'Welcome to my text editor!!!!!!!!!!!!!!'
                    padding = ' ' * ((self.dimensions.columns - len(welcome_msg)) // 2)
                    self.append_outbuf(padding + welcome_msg)

            self.append_outbuf('\r\n')

    # row operations
    def rowInsertChar(self, ch):
        if self.cx < 0 or self.cx > len(self.erows[self.cy]):
            self.cx = len(self.erows[self.cy])
        new_string = [x for x in self.erows[self.cy]]
        new_string = new_string[:self.cx] + [ch] + new_string[self.cx:]
        self.erows[self.cy] = ''.join(new_string)

    def editorInsertChar(self, ch):
        if self.cy == len(self.erows):
            self.erows.append("")

        self.rowInsertChar(ch)
        self.incrementx()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print('Error: too many arguments provided')
        sys.exit()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
    else:
        arg = None

    jin = Jin(arg)
