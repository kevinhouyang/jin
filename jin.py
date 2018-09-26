class JinRow():
    """Row of text, handles deleting and insert characters"""
    def __init__(self, data=[]):
        self.data = data

    def insertChar(self, char, index):
        self.data.insert(index, char)

    def deleteChar(self, index):
        self.data.pop(index)

    def lineBreak(self, index):
        result = self.data[index:]
        self.data = self.data[:index]
        return result

    def string(self):
        return ''.join(self.data)

    def length(self):
        return len(self.data)

class JinTextEdit():
    """processes keypresses, maintains cursor position, and handles scrolling"""

    def __init__(self, columns, lines,rows=[]):
        self.cursorX, self.cursorY = 0, 0
        if rows:
            self.body = [JinRow(list(row)) for row in rows]
        else:
            self.body = [JinRow([])]
        self.columns = columns
        self.lines = lines
        self.verticalScroll = 0
        self.horizontalScroll = 0

    def getCursorX(self):
        return self.cursorX

    def getCursorY(self):
        return self.cursorY

    def getVerticalScroll(self):
        return self.verticalScroll

    def getHorizontalScroll(self):
        return self.horizontalScroll

    def numRows(self):
        return len(self.body)

    def processKeypress(self, key):
        currentRow = self.cursorY + self.verticalScroll
        currentCol = self.cursorX + self.horizontalScroll

        if key == "ENTER":
            chunk = self.body[currentRow].lineBreak(currentCol)
            self.body.insert(currentRow + 1, JinRow(chunk))
            self.incrementY()
            self.cursorX = 0
            self.horizontalScroll = 0
        elif key == "BACKSPACE":
            self.body[currentRow].deleteChar(currentCol)
            self.decrementX()
        elif key == "UP":
            self.decrementY()
        elif key == "DOWN":
            self.incrementY()
        elif key == "RIGHT":
            self.incrementX()
        elif key == "LEFT":
            self.decrementX()
        else:
            self.body[currentRow].insertChar(key, currentCol)
            self.incrementX()

    def decrementX(self):
        if self.cursorX:
            self.cursorX -= 1
        elif self.horizontalScroll:
            self.horizontalScroll -= 1

    def incrementX(self):
        currentRow = self.cursorY + self.verticalScroll
        if self.cursorX < min(self.columns, self.body[currentRow].length()):
            self.cursorX += 1
        elif self.cursorX + self.horizontalScroll < self.body[currentRow].length():
            self.horizontalScroll += 1

    def decrementY(self):
        if self.cursorY:
            self.cursorY -= 1
        elif self.verticalScroll:
            self.verticalScroll -= 1

        self.cursorX = min(self.cursorX, self.body[self.cursorY + self.verticalScroll].length())
        self.horizontalScroll = 0

    def incrementY(self):
        if self.cursorY < self.lines - 1:
            self.cursorY += 1
        elif self.cursorY + self.verticalScroll < self.numRows() - 1:
            self.verticalScroll += 1

        self.cursorX = min(self.cursorX, self.body[self.cursorY + self.verticalScroll].length())
        self.horizontalScroll = 0

    def saveString(self):
        return '\n'.join([row.string() for row in self.body])

    def string(self):
        output = []
        numRows = min(self.numRows(), self.lines)
        for i in range(numRows):
            output.append(
                self.body
                    [i + self.verticalScroll].string()
                    [self.horizontalScroll : self.horizontalScroll + self.columns]
                )
        return '\r\n'.join(output)

class StatusBar():
    """status bar that displays information and messages to the user"""
    def __init__(self, filename, columns, lines, editor):
        self.editor = editor
        numRows = self.numRows()
        currRow = self.currRow()
        if filename:
            self.filename = filename
        else:
            self.filename = "[No Name]"

        self.userMsg = ""
        self.colSpacing = self.colGenerator(columns)
        self.lines = lines

    def colGenerator(self, columns):
        def generator(msgLength):
            return " " * (columns - msgLength)
        return generator

    def rowSpacing(self):
        return '\r\n' * (self.lines - self.numRows() - 1)

    def setUserMsg(self, msg):
        self.userMsg = msg

    def currRow(self):
        return self.editor.getCursorY() + self.editor.getVerticalScroll() + 1

    def numRows(self):
        return self.editor.numRows()

    def statusMsg(self):
        return "{} - {} lines".format(self.filename, self.numRows())

    def rowMsg(self):
        return "{}/{}".format(self.currRow(), self.numRows())

    def string(self):
        return ( '\x1b[7m'
            + self.rowSpacing()
            + self.statusMsg() + self.colSpacing(len(self.statusMsg()) + len(self.rowMsg()))
            + self.rowMsg()
            + self.userMsg + self.colSpacing(len(self.userMsg))
            + '\x1b[m')

import sys
import termios
from curses.ascii import ctrl
class Jin():
    """handles terminal input/output, manages window, reads input"""

    def __init__(self, filename=""):
        import shutil
        self.dimensions = shutil.get_terminal_size() # stored as (columns, lines)
        if filename:
            fd = open(filename, 'r')
            self.editor = JinTextEdit(
                self.dimensions.columns,
                self.dimensions.lines - 2, # minus two to leave room for status bar
                fd.read().splitlines())
            fd.close()
            self.dirtyFlag = False
        else:
            self.editor = JinTextEdit(
                columns=self.dimensions.columns,
                lines=self.dimensions.lines - 2) # minus two to leave room for status bar
            self.dirtyFlag = True
            filename = "new.txt"

        self.filename = filename
        self.statusBar = StatusBar(
            filename,
            self.dimensions.columns,
            self.dimensions.lines - 1,
            self.editor)
        self.enableRaw()

        while(True):
            self.updateScreen()
            self.readKeypress()

    def enableRaw(self):
        import tty, atexit
        defaultAttr = termios.tcgetattr(sys.stdin.fileno())
        tty.setraw(sys.stdin.fileno())
        atexit.register(
            lambda:termios.tcsetattr(
                sys.stdin.fileno(),
                termios.TCSAFLUSH,
                defaultAttr
                )
            )

    def updateScreen(self):
        outbuf = [
            '\x1b[?25l', # disappears cursor
            '\x1b[H' # moves cursor to top left of screen
            '\x1b[2J', # clears screen
            self.editor.string(),
            '\r\n',
            self.statusBar.string(),
            '\x1b[{};{}H'.format( # positions cursor
                self.editor.getCursorY() + 1,
                self.editor.getCursorX() + 1
                ),
            '\x1b[?25h' # reappears cursor
            ]
        sys.stdout.write(''.join(outbuf))
        sys.stdout.flush()

    def readKeypress(self):
        i = sys.stdin.read(1)

        if i == ctrl('q'):
            self.quit()
            return
        elif i == ctrl('s'):
            self.save()
            return

        self.dirtyFlag = True

        if i[0] == '\x1b':
            i = sys.stdin.read(2)
            inputSwitcher = {
                'A': 'UP',
                'B': 'DOWN',
                'C': 'RIGHT',
                'D': 'LEFT',
            }
            i = inputSwitcher[i[1]]
        elif ord(i) == 127:
            i = 'BACKSPACE'
        elif ord(i) == 13:
            i = 'ENTER'

        self.editor.processKeypress(i)

    def save(self):
        if self.filename:
            fd = open(self.filename, 'w')
            fd.write(self.editor.saveString())
            fd.close()
            self.dirtyFlag = False
            self.statusBar.setUserMsg("Saved file as " + self.filename)
        # else:
            # self.statusBar.setUserMsg("Save new file: ")

    def quit(self):
        if not self.dirtyFlag:
            sys.exit()
        else:
            self.statusBar.setUserMsg("Are you sure you want to quit? You haven't saved. Press ctrl q again to quit.")
            self.dirtyFlag = False

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print('Error: too many arguments provided')
        sys.exit()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
    else:
        arg = None

    jin = Jin(arg)
