#!/usr/bin/env python

import os
import sys
import copy     # to duplicate board objects
import random   # for portals and random devices
import argparse # for command line arguments
import termios  # for unbuffered stdin
from threading import Thread # for non-blocking stdin
try:
    from Queue import Queue, Empty # for non-blocking stdin
except ImportError:
    from queue import Queue, Empty  # python 3.x



oct_digits = '01234567'
hex_digits = '0123456789ABCDEF'
b36_digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

parser = argparse.ArgumentParser(description='Interpret a Marbelous file.')

parser.add_argument('file', metavar='filename.mbl',
                    help='filename for the main board file')
parser.add_argument('inputs', metavar='input', nargs='*', 
                    help='inputs for the main board')
parser.add_argument('-r', '--return', dest='return', action='store_true',
                    help='main board {0 as process return code')
parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                    help='operate in verbose mode, -vv -vvv -vvvv increase verbosity')
parser.add_argument('--stderr', dest='stderr', action='store_true',
                    help='send verbose output to stderr instead of stdout')

options = vars(parser.parse_args())

verbose_stream = sys.stderr if options['stderr'] else sys.stdout

def unbuffered_getch(stream):
    try:
        import msvcrt
    except:
        fd = stream.fileno()
        # temporarily unbuffer stdin if it's a tty
        if os.isatty(fd):
            old_settings = termios.tcgetattr(fd)
            new_settings = termios.tcgetattr(fd)
            try:
                new_settings[3] = new_settings[3] & ~termios.ICANON # leave canonical mode
                termios.tcsetattr(fd, termios.TCSANOW, new_settings)
                ch = stream.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSANOW, old_settings)
        else:
            ch = stream.read(1)
    else:
        ch = msvcrt.getch()
    return ch

def enqueue_input(stream, queue):
    for char in iter(lambda:unbuffered_getch(stream), b''):
        queue.put(char)

stdin_queue = Queue()
stdin_thread = Thread(target=enqueue_input, args=(sys.stdin, stdin_queue))
stdin_thread.daemon = True # thread dies with the program
stdin_thread.start()

devices = set([
    '  ',
    '..',
    '\\\\',
    '//',
    '\\/',
    '/\\',
    '++',
    '--',
    '!!',
    '??',
    '{<',
    '{>',
    '<<',
    '>>',
    '~~',
    ']]'
    ])
# devices with variations for 36 constants
for p in '=><-+?@&}{':
    for d in b36_digits:
        devices.add(p+d)
# bit fetch devices
for d in oct_digits:
    devices.add('^'+d)

def format_cell(x):
    return '..' if x is None else hex(x)[2:].upper().zfill(2) if type(x) is int else x.ljust(2)

class Board:
    def __init__(self):
        # hash of (inputnumber):[(x,y),(x,y)...]
        self.inputs = {}
        self.outputs = {}
        self.function_width = 1
        self.board_h = 0
        self.board_w = 0
        self.marbles = []
        self.devices = []
        self.functions = []
        self.print_out = ''
        self.recursion_depth = 0
        self.tick_count = 0
        self.name = ''
        self.function_queue = []

    def __repr__(self):
        return "Board name=" + self.name + " tick=" + str(self.tick_count)

    def printr(self, s):
        verbose_stream.write( (' ' * self.recursion_depth + str(s)) + '\n')

    def display_tick(self):
        if self.function_queue:
            board, coordinates = self.function_queue[-1]
            board.display_tick()
        else:
            self.display()

    def display(self):
        self.printr(':' + self.name + " tick " + str(self.tick_count))
        for y in range(self.board_h):
            line = ''
            for x in range(self.board_w):
                line += (format_cell(self.marbles[y][x]) if self.marbles[y][x] is not None else format_cell(self.devices[y][x])) + ' '
            self.printr(line)

    def parse(self, input):
        board = []
        for line in input:
            line = line.rstrip()
            if len(line) < 3 or line[2] != ' ': # split every 2 characters
                row = [line[i:i+2] for i in range(0, len(line), 2)]
            else:
                if line[3] != ' ': # split on one space
                    row = line.split(' ')
                else: # split on two spaces
                    row = line.split('  ')
            # support for simple comments
            # strip everything past the first "#"
            for i in range(len(row)):
                if row[i][0] == "#":
                    row = row[:i]
                    break
                if "#" in row[i]:
                    row[i] = row[i][:row[i].index("#")]
                    row = row[:i+1]
                    break
            board.append(row)
            self.board_w = max(self.board_w, len(row))
            self.board_h += 1
        mbl = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        dev = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        for y in range(self.board_h):
            for x in range(self.board_w):
                if x >= len(board[y]):
                    b = '  '
                else:
                    b = board[y][x]
                if b is None:
                    continue
                elif b[0] in hex_digits and b[1] in hex_digits:
                    mbl[y][x] = int(b, 16)
                else:
                    dev[y][x] = b
                    if b[0] == '}' and b[1] in b36_digits:
                        num = int(b[1], 36)
                        if num not in self.inputs:
                            self.inputs[num] = []
                        self.inputs[num].append((y, x))
                    elif b[0] == '{' and (b[1] in b36_digits or b[1] == '<' or b[1] == '>'):
                        if b[1] in b36_digits:
                            num = int(b[1], 36)
                        elif b[1] == '<':
                            num = -1
                        elif b[1] == '>':
                            num = -2
                        if num not in self.outputs:
                            self.outputs[num] = []
                        self.outputs[num].append((y, x))
        self.marbles = mbl
        self.devices = dev
        self.function_width = 1
        if len(self.inputs) > 0:
            self.function_width = max(self.function_width, max(self.inputs.keys())+1)
        if len(self.outputs) > 0:
            self.function_width = max(self.function_width, max(self.outputs.keys())+1)
        if self.name != "MB" and (self.function_width*2) % len(self.name) != 0:
            sys.stderr.write("Board name " + str(self.name) + " not a divisor of width " + str(self.function_width) + '\n')
            exit(1)

    def find_functions(self):
        wide_function_names = dict([(b.name * (2 * b.function_width / len(b.name)), b.name) for b in boards.values()])
        name_so_far = ''
        for y in range(self.board_h):
            for x in range(self.board_w):
                b = self.devices[y][x]
                if name_so_far == '':
                    if b is None or b in devices or (b[0] in hex_digits and b[1] in hex_digits):
                        continue
                name_so_far += b
                if name_so_far in wide_function_names:
                    self.functions.append((y, x-(len(name_so_far)-1)/2, wide_function_names[name_so_far]))
                    name_so_far = ''
            if name_so_far != '':
                sys.stderr.write("Board " + str(self.name) + " row  " + str(y) + " ends with unexpected cells: " + str(name_so_far) + "\n")
                exit(1)

    def populate_inputs(self, inputs):
        for input_num,value in inputs.iteritems():
            if value is not None:
                for y, x in self.inputs[input_num]:
                    self.marbles[y][x] = value

    def get_output_values(self):
        outputs = {}
        for output_num, coordinates in self.outputs.items():
            for y, x in coordinates:
                if self.marbles[y][x] is not None:
                    if output_num not in outputs:
                        outputs[output_num] = self.marbles[y][x]
                    else:
                        outputs[output_num] += self.marbles[y][x]
        return outputs

    def all_outputs_filled(self):
        if not self.outputs:
            return False
        for output_set in self.outputs.values():
            output_filled = False
            for y, x in output_set:
                if self.marbles[y][x] is not None:
                    output_filled = True
                    break
            if not output_filled:
                return False
        return True

    def tick(self):
        if self.all_outputs_filled() and not self.function_queue:
            if options['verbose'] > 1:
                self.printr("Exiting board " + str(self.name) + " on tick " + str(self.tick_count) + " due to filled { devices")
            return False

        mbl = self.marbles
        def put_immediate(y, x, m):
            mbl[y][x] = (m % 256) if not mbl[y][x] else (mbl[y][x]+m) % 256
        if self.function_queue:
            #TODO: use a deque so we can run functions in "correct" order
            board, coordinates = self.function_queue[-1]
            y, x = coordinates
            if not board.tick():
                for location, value in board.get_output_values().items():
                    if location == -1:
                        if x-1 >= 0:
                            put_immediate(y, x-1, value)
                    elif location == -2:
                        if x+board.function_width < self.board_w:
                            put_immediate(y, x+board.function_width, value)
                    else:
                        if y == self.board_h-1:
                            if options['verbose'] > 0:
                                self.print_out += chr(value)
                            if options['verbose'] > 1:
                                self.printr("STDOUT: " + "0x" + hex(value)[2:].upper().zfill(2) + \
                                            '/"' + (chr(value) if value > 31 else '?') + '"')
                            if options['verbose'] == 0 or options['stderr']:
                                sys.stdout.write(chr(value))
                        else:
                            put_immediate(y+1, x+int(location), value)
                self.function_queue.pop()
                self.print_out += board.print_out
                if options['verbose'] > 2:
                    board.display()
            return True

        self.tick_count += 1
        dev = self.devices
        # new marble array
        nmb = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        exit_now = False
        hidden_activity = False

        def put(y, x, m):
            nmb[y][x] = (m % 256) if not nmb[y][x] else (nmb[y][x]+m) % 256

        #TODO: queue print_out and sort it correctly with function print_out
        # process each marble
        for y in range(self.board_h):
            for x in range(self.board_w):
                m = mbl[y][x]
                i = dev[y][x]
                l = 0  # move left?
                r = 0  # move right?
                d = 0  # move down?
                new_x = None
                new_y = None
                if m is None:  # no marble
                    continue
                elif i:  # device
                    if i == '..' or i == '  ':  # fall
                        d = 1
                    elif i == '\\\\':  # divert right
                        r = 1
                    elif i == '//':  # divert left
                        l = 1
                    elif i == '/\\':  # split
                        r = 1
                        l = 1
                    elif i == '\\/':  # trash
                        pass
                    elif i == '++':  # increment
                        d = 1
                        m += 1
                    elif i == '--':  # decrement
                        d = 1
                        m -= 1
                    elif i == '<<': # shift left
                        d = 1
                        m = m << 1
                    elif i == '>>': # shift right
                        d = 1
                        m = m >> 1
                    elif i == '~~': # invert bits / logical not
                        d = 1
                        m = ~m
                    elif i == ']]': # invert bits / logical not
                        try:
                            char = stdin_queue.get_nowait()
                        except Empty: # no bytes pending from stdin
                            r = 1
                        else: # got a byte from stdin
                            m = ord(char)
                            d = 1
                    elif i[0] == '^' and i[1] in oct_digits:  # fetch a bit
                        s = int(i[1], 8)
                        d = 1
                        m = (m & (1 << s)) > 0
                    elif i[0] == '+' and i[1] in b36_digits:  # add a constant
                        s = int(i[1], 36)
                        d = 1
                        m = m + s
                    elif i[0] == '-' and i[1] in b36_digits:  # subtract a constant
                        s = int(i[1], 36)
                        d = 1
                        m = m - s
                    elif i[0] == '=' and i[1] in b36_digits:  # equals a constant?
                        s = int(i[1], 36)
                        if m == s:
                            d = 1
                        else:
                            r = 1
                    elif i[0] == '>' and i[1] in b36_digits:  # greater than a constant?
                        s = int(i[1], 36)
                        if m > s:
                            d = 1
                        else:
                            r = 1
                    elif i[0] == '<' and i[1] in b36_digits:  # less than a constant?
                        s = int(i[1], 36)
                        if m < s:
                            d = 1
                        else:
                            r = 1
                    elif i[0] == '?' and (i[1] in b36_digits or i[1] == '?'):  # random number, 0-static or 0-marble
                        if i[1] != '?':
                            s = int(i[1], 36)
                        else:
                            s = m
                        m = random.randint(0, s)
                        d = 1
                    elif i[0] == '@' and i[1] in b36_digits:  # portal
                        s = int(i[1], 36)
                        other_portals = []
                        for k in range(self.board_h):
                            for j in range(self.board_w):
                                if (k != y or j != x) and \
                                    dev[k][j] and \
                                    dev[k][j][0] == '@' and \
                                    dev[k][j][1] == i[1]:
                                    other_portals.append((k, j))
                        if other_portals:
                            new_y, new_x = random.choice(other_portals)
                            d = 1
                        else:
                            d = 1
                    elif i[0] == '&' and i[1] in b36_digits:  # synchronize
                        if m is not None:
                            s = int(i[1], 36)
                            release = True
                            for k in range(self.board_h):
                                for j in range(self.board_w):
                                    if (k != y or j != x) and \
                                        dev[k][j] and \
                                        dev[k][j][0] == '&' and \
                                        dev[k][j][1] == i[1] and \
                                        mbl[k][j] is None:
                                        release = False
                            if release is False:
                                put(y, x, m)
                            else:
                                d = 1
                    elif i[0] == '{' and (i[1] in b36_digits or i[1] == '<' or i[1] == '>'):  # output
                        put(y, x, m)
                    elif i[0] == '}' and i[1] in b36_digits:  # input == fall
                        d = 1
                    elif i == '!!':  # exit
                        exit_now = True
                    else:  # unrecognized device
                        pass  # default to trash!
                else:  # no device
                    d = 1
                new_y = new_y if new_y is not None else y
                new_x = new_x if new_x is not None else x
                if d:
                    if new_y == self.board_h-1:
                        if options['verbose'] > 0:
                            self.print_out += chr(m)
                        if options['verbose'] > 1:
                            self.printr("STDOUT: " + "0x" + hex(m)[2:].upper().zfill(2) + \
                                        '/"' + (chr(m) if m > 31 else '?') + '"')
                        if options['verbose'] == 0 or options['stderr']:
                            sys.stdout.write(chr(m))
                        hidden_activity = True
                    else:
                        put(new_y+1, new_x, m)
                if r:
                    if new_x < self.board_w-1:
                        put(new_y, new_x+1, m)
                if l:
                    if new_x > 0:
                        put(new_y, new_x-1, m)

        for y, x, name in self.functions:
            run = True
            sub_board = boards[name]
            for i in sub_board.inputs:
                if self.marbles[y][x+i] is None:
                    run = False
                    break
            if run:
                hidden_activity = True
                self.function_queue.append((copy.deepcopy(sub_board), (y, x)))
                inputs = {}
                for i in range(sub_board.function_width):
                    inputs[i] = self.marbles[y][x+i]
                self.function_queue[-1][0].populate_inputs(inputs)
                self.function_queue[-1][0].recursion_depth = self.recursion_depth+1
            else:
                for i in range(sub_board.function_width):
                    if self.marbles[y][x+i] is not None:
                        put(y, x+i, self.marbles[y][x+i])

        diff = sum([cmp(x, y) != 0 for x, y in zip(self.marbles, nmb)])
        if diff == 0 and hidden_activity is False:
            if options['verbose'] > 1:
                self.printr("Exiting board " + str(self.name) + " on tick " + str(self.tick_count) + " due to lack of activity")
            return False
        if exit_now:
            if options['verbose'] > 1:
                self.printr("Exiting board " + str(self.name) + " on tick " + str(self.tick_count) + " due to filled X devices")
            return False
        self.marbles = nmb
        return True

# the boards array contains pristine instances of boards from the source
boards = {}

def load_mbl_file(filename,ignore_main=True):
    lines = []
    main_skipped = False
    with open(filename) as f:
        for line in f.readlines():
            line = line.rstrip()
            if len(line)>9 and line[0:9] == "#include ":
                script_dir = os.path.dirname(options['file'])
                lines.extend(load_mbl_file(os.path.join(script_dir,line[9:])))
            if ignore_main and not main_skipped:
                if len(line) > 0 and line[0] == ':':
                    main_skipped = True
                else:
                    continue
            if len(line)<2 or line[0] == '#':  # comment
                continue
            lines.append(line)
    return lines

loaded_lines = load_mbl_file(options['file'],ignore_main=False)

thisboard = Board()
boardname = "MB"
boards[boardname] = thisboard
thisboard.name = boardname
parse_lines = []
for line in loaded_lines:
    if line[0] == ':':  # start of new named board
        thisboard.parse(parse_lines)
        thisboard = Board()
        boardname = line[1:].rstrip()
        boards[boardname] = thisboard
        thisboard.name = boardname
        parse_lines = []
    else:  # another line in the current board
        parse_lines.append(line)
thisboard.parse(parse_lines)

# can't process function devices before all the functions in the file are loaded
for b in boards.values():
    b.find_functions()

# make a copy of board zero as the main board
board = copy.deepcopy(boards['MB'])

if len(options['inputs']) != len(board.inputs):
    sys.stderr.write(options['file'] + " expects " + str(len(board.inputs)) + " inputs, you gave " + str(len(options['inputs'])) + "\n")
    exit(1)

board.populate_inputs(dict(enumerate([int(x) for x in options['inputs']])))

if options['verbose'] > 2:
    board.display_tick()

while board.tick():# and board.tick_count < 10000:
    if options['verbose'] > 2:
        board.display_tick()

if options['verbose'] > 0:
    board.printr("STDOUT: " + ' '.join(["0x" + hex(ord(v))[2:].upper().zfill(2) + \
                '/"' + (v if ord(v) > 31 else '?') + '"' \
                for v in board.print_out]))

outputs = board.get_output_values()
if options['verbose'] > 0:
    if len(board.outputs):
        out_str = "MB Outputs: " + \
            ' '.join(['{' + str(n) + '=' + \
                str(v) + "/0x" + hex(v)[2:].upper().zfill(2) + \
                '/"' + (chr(v) if v > 31 else '?') + '"' \
                for n,v in sorted(outputs.iteritems())])
        print out_str

if options['return']:
    if len(board.outputs):
        if 0 in outputs:
            exit_code = outputs[0]
        else:
            exit_code = 0
        exit(exit_code)
