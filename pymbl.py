#!/usr/bin/env python

import sys
import copy
import random

if len(sys.argv)<2:
    print "pymbl.py foo.mbl [I0] [I1] [...]\n"
    exit(-1)

mblfile = sys.argv[1]
hex_digits = '0123456789ABCDEF'
b36_digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def print_cell(x):
    return '..' if x==None else hex(x)[2:].upper().zfill(2) if type(x) is int else x.ljust(2)

class Board:
    def __init__(self):
        # hash of (inputnumber):[(x,y),(x,y)...]
        self.inputs = {}
        self.outputs = {}
        self.functionwidth = 1
        self.board_h = 0
        self.board_w = 0
        self.marbles = []
        self.instructions = []
        self.functions = []
        self.print_out = ''
        self.recursiondepth = 0
        self.tick_count = 0
        self.name = ''
    def printr(self,s):
        print ' ' * self.recursiondepth + str(s)
    def display(self):
        self.printr(self.name + " tick: " + str(self.tick_count))
        for y in range(self.board_h):
            line = ''
            for x in range(self.board_w):
                line += (print_cell(self.marbles[y][x]) if self.marbles[y][x]!=None else print_cell(self.instructions[y][x])) + ' '
            self.printr(line)
            # print ' '.join([print_cell(x) for x in self.marbles[y]])
            # print ' '.join([print_cell(x) for x in self.instructions[y]])
    def parse(self,input):
        board = []
        for line in input:
            row = line.rstrip().split(' ')
            board.append(row)
            self.board_w = max(self.board_w,len(row))
            self.board_h += 1
        # print self.board_h, self.board_w
        mbl = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        ins = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        for y in range(self.board_h):
            for x in range(self.board_w):
                b = board[y][x]
                # print y, x, b
                if b == '..' or b == '  ' or b == None:
                    continue
                elif b[0] in hex_digits and b[1] in hex_digits:
                    mbl[y][x] = int(b,16)
                else:
                    ins[y][x] = b
                    if b[0] == 'I':
                        num = int(b[1],36)
                        if num not in self.inputs:
                            self.inputs[num] = []
                        self.inputs[num].append((y,x))
                    elif b[0] == 'O':
                        if b[1] in b36_digits:
                            num = int(b[1],36)
                        elif b[1] == '<':
                            num = -1
                        elif b[1] == '>':
                            num = -2
                        if num not in self.outputs:
                            self.outputs[num] = []
                        self.outputs[num].append((y,x))
        self.marbles = mbl
        self.instructions = ins
        self.functionwidth = 1
        if len(self.inputs) > 0:
            self.functionwidth = max(self.functionwidth,max(self.inputs.keys())+1)
        if len(self.outputs) > 0:
            self.functionwidth = max(self.functionwidth,max(self.outputs.keys())+1)
    def find_functions(self):
        infunc = 0
        for y in range(self.board_h):
            for x in range(self.board_w):
                b = self.instructions[y][x]
                if infunc > 0 and b != self.instructions[y][x-1]:
                    self.printr("Wrong number of " + b + " on row " + str(y))
                if b in boards:
                    if infunc == 0:
                        self.functions.append((y,x))
                        infunc = boards[b].functionwidth-1
                        # print "Starting a block of " + b + " and looking for " + str(infunc) + " more."
                    else:
                        infunc -= 1
        if infunc > 0:
            self.printr("Wrong number of " + str(b) + " on row " + str(self.board_h-1))

    def populate_input(self,n,m):
        # print n,m
        count = 0
        if self.inputs[n]:
            for y,x in self.inputs[n]:
                self.marbles[y][x] = m
                count += 1
        return count
    def get_output(self,n):
        out = 0
        if n in self.outputs and self.outputs[n]:
            for y,x in self.outputs[n]:
                if self.marbles[y][x] != None:
                    out += self.marbles[y][x]
        else:
            return None
        return out%256
    def tick(self):
        # self.printr(str(self.marbles))
        mbl = self.marbles
        ins = self.instructions
        # new marble array
        nmb = [[None for x in range(self.board_w)] for y in range(self.board_h)]
        exit_now = False
        hidden_activity = False
        # print mbl
        # process each marble
        for y in range(self.board_h):
            for x in range(self.board_w):
                def put(y,x,m):
                    # self.printr("put " + str(y) + " " + str(x) + " " + str(m))
                    nmb[y][x] = (m%256) if not nmb[y][x] else (nmb[y][x]+m)%256
                m = mbl[y][x]
                i = ins[y][x]
                l = 0 # move left?
                r = 0 # move right?
                d = 0 # move down?
                new_x = None
                new_y = None
                # print str(m) + "|" + str(y) + " " + str(x)
                # print "considering " + print_cell(m) + " at " + str(y) + " " + str(x)
                if m == None: # no marble
                    continue
                elif i: # instruction
                    if i == '\\\\': # divert right
                        r = 1
                    elif i == '//': # divert left
                        l = 1
                    elif i == '/\\': # split
                        r = 1
                        l = 1
                    elif i == '\\/': # trash
                        pass
                    elif i == '++': # increment
                        d = 1
                        m = m
                    elif i == '--': # decrement
                        d = 1
                        m -= 1
                    elif i[0] == '=' and (i[1] in b36_digits or i[1] == '?'): # equals state or constant?
                        if i[1] != '?':
                            s = int(i[1],36)
                        if m == s:
                            r = 1
                        else:
                            d = 1
                    elif i[0] == '>' and (i[1] in b36_digits or i[1] == '?'): # greater than state or constant?
                        if i[1] != '?':
                            s = int(i[1],36)
                        if m > s:
                            r = 1
                        else:
                            d = 1
                    elif i[0] == '<' and (i[1] in b36_digits or i[1] == '?'): # less than state or constant?
                        if i[1] != '?':
                            s = int(i[1],36)
                        if m < s:
                            r = 1
                        else:
                            d = 1
                    elif i[0] == 'R' and (i[1] in b36_digits or i[1] == '?'): # random number, 0-static or 0-marble
                        if i[1] != '?':
                            s = int(i[1],36)
                        else :
                            s = m
                        m = random.randint(0,s)
                        d = 1
                    elif i[0] == 'P' and i[1] in b36_digits: # portal
                        s = int(i[1],36)
                        other_portals = []
                        for k in range(self.board_h):
                            for j in range(self.board_w):
                                if (k!=y or j!=x) and \
                                    ins[k][j] and \
                                    ins[k][j][0] == 'P' and \
                                    ins[k][j][1] == i[1]:
                                    other_portals.append((k,j))
                        if other_portals:
                            new_y,new_x=random.choice(other_portals)
                            d = 1
                        else:
                            d = 1
                    elif i[0] == 'S' and i[1] in b36_digits: # synchronize
                        if m != None:
                            s = int(i[1],36)
                            # print "sync " + str(s) + " at " + str(y) + " " + str(x) + "?"
                            release = True
                            for k in range(self.board_h):
                                for j in range(self.board_w):
                                    # print x,y,m,k,j,ins[k][j],mbl[k][j]
                                    if (k!=y or j!=x) and \
                                        ins[k][j] and \
                                        ins[k][j][0] == 'S' and \
                                        ins[k][j][1] == i[1] and \
                                        mbl[k][j] == None:
                                        # print "nothing at " + str(k) + " " + str(j)
                                        release = False
                            if release == False:
                                put(y,x,m)
                            else:
                                d = 1
                            # else:
                                # print "unpause!"
                    elif i[0] == 'O' and i[1] in b36_digits: # output
                        put(y,x,m)
                    elif i == 'XX': # exit
                        exit_now = True
                    elif i in boards:
                        pass
                    else: # unrecognized instruction or Input
                        d = 1
                else: # no instruction
                    d = 1
                new_y = new_y if new_y!=None else y
                new_x = new_x if new_x!=None else x
                # self.printr(str((y,x,d,r,l)))
                if d:
                    if new_y==self.board_h-1:
                        self.print_out += hex(m)[2:].upper().zfill(2) + '(' + (chr(m) if m > 32 else '?') + ') '
                        hidden_activity = True
                    else:
                        put(new_y+1,new_x,m)
                if r:
                    if new_x < self.board_w-1:
                        put(new_y,new_x+1,m)
                if l:
                    if new_x > 0:
                        put(new_y,new_x-1,m)
        for c in self.functions:
            run = True
            g = boards[ins[c[0]][c[1]]]
            for i in g.inputs:
                if mbl[c[0]][c[1]+i] == None:
                    run = False
            if run:
                f = copy.deepcopy(g)
                f.recursiondepth = self.recursiondepth+1
                for i in g.inputs:
                    f.populate_input(i,mbl[c[0]][c[1]+i])
                f.display()
                while f.tick():
                    f.display()
                self.print_out += f.print_out
                if f.get_output(-1) != None and c[1] > 0:
                    put(c[0],c[1]-1,f.get_output(-1))
                if f.get_output(-2) != None and c[1]+f.functionwidth < self.board_w:
                    put(c[0],c[1]+f.functionwidth,f.get_output(-2))
                for o in sorted(f.outputs.keys()):
                    if o < 0:
                        continue
                    if f.get_output(o) != None:
                        if c[0] < self.board_h-1:
                            put(c[0]+1,c[1]+o,f.get_output(o))
                            # print "put " + str(f.get_output(o))
                        else:
                            self.print_out += hex(m)[2:].zfill(2) + '(' + (chr(m) if m > 32 else '?') + ') '
                            hidden_activity = True
            else:
                for i in range(g.functionwidth):
                    if mbl[c[0]][c[1]+i] != None:
                        put(c[0],c[1]+i,mbl[c[0]][c[1]+i])
        self.tick_count += 1
        diff = sum([cmp(x,y)!=0 for x,y in zip(self.marbles,nmb)])
        if diff == 0 and hidden_activity == False:
            self.printr("Exiting board due to lack of activity")
            return False
        self.marbles = nmb
        if len(self.outputs):
            outputs_filled = True
            for o in self.outputs.values():
                this_output_filled = False
                for c in o:
                    if nmb[c[0]][c[1]] != None:
                        this_output_filled = True
                if this_output_filled == False:
                    outputs_filled = False
            if outputs_filled:
                self.printr("Exiting board due to filled O instructions")
                return False
        if exit_now:
            self.printr("Exiting board due to filled X instruction")
            return False
        return True

# the boards array contains pristine instances of boards from the source
boards = {}

with open(mblfile) as f:
    thisboard = Board()
    boardname = "MB"
    boards[boardname]=thisboard
    thisboard.name = boardname
    lines = []
    for line in f.readlines():
        if len(line.rstrip()) == 3 and line[2] == ':':
            thisboard.parse(lines)
            thisboard = Board()
            boardname = line[0:2]
            boards[boardname]=thisboard
            thisboard.name = boardname
            lines = []
        else:
            lines.append(line)
    thisboard.parse(lines)

# can't process function devices before all the functions in the file are loaded
for b in boards.values():
    b.find_functions()

# make a copy of board zero as the main board
board = copy.deepcopy(boards['MB'])

if len(sys.argv)-2 != len(board.inputs):
    print sys.argv[1] + " expects " + str(len(board.inputs)) + " inputs, you gave " + str(len(sys.argv)-2)
    exit(1)

for i in range(2,len(sys.argv)):
    board.populate_input(i-2,int(sys.argv[i]))

board.display()

while board.tick() and board.tick_count < 1000:
    board.display()

print board.print_out

if len(board.outputs):
    for n in board.outputs:
        if board.outputs[n]:
            o = board.get_output(n)
            print str(o) + '(' + chr(o) + ') '
