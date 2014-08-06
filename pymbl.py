#!/usr/bin/env python

import sys
import copy
import random

if len(sys.argv)<2:
	print "pymbl.py foo.mbl [I0] [I1] [...]\n"
	exit(-1)

mblfile = sys.argv[1]
hex_digits = '0123456789ABCDEF'
stateful_instructions = ['<','=','>','P','T','S','R','O']

def print_cell(x):
	return '..' if x==None else hex(x)[2:].zfill(2) if type(x) is int else x.ljust(2)

class Board:
	def __init__(self):
		self.input_count = 0
		self.inputs = []
		self.inputcoords = {}
		self.output_count = 0
		self.outputs = []
		self.outputcoords = {}
		self.exit_count = 0
		self.exitcoords = {}
		self.board_h = 0
		self.board_w = 0
		self.marbles = []
		self.instructions = []
		self.state = []
		self.subroutines = []
		self.print_out = ''
	def display(self):
		for y in range(self.board_h):
			line = ''
			for x in range(self.board_w):
				line += (print_cell(self.marbles[y][x]) if self.marbles[y][x]!=None else print_cell(self.instructions[y][x])) + ' '
			print line
			# print ' '.join([print_cell(x) for x in self.marbles[y]])
			# print ' '.join([print_cell(x) for x in self.instructions[y]])
			# print ' '.join([print_cell(x) for x in self.state[y]])

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
		sta = [[0 for x in range(self.board_w)] for y in range(self.board_h)]
		sub = [[None for x in range(self.board_w)] for y in range(self.board_h)]
		for y in range(self.board_h):
			for x in range(self.board_w):
				b = board[y][x]
				if b == '..' or b == None:
					continue
				elif b[0] in hex_digits and b[1] in hex_digits:
					mbl[y][x] = int(b,16)
				else:
					ins[y][x] = b
					if b[0] in stateful_instructions and b[1] != '?':
						sta[y][x] = int(b[1],36)
					if b[0] == 'I':
						self.input_count += 1
						self.inputcoords[int(b[1],36)]=(y,x)
					if b[0] == 'O':
						self.output_count += 1
						self.outputcoords[int(b[1],36)]=(y,x)
					if b[0] == 'X':
						self.exit_count += 1
						self.exitcoords[int(b[1],36)]=(y,x)
		self.marbles = mbl
		self.instructions = ins
		self.state = sta
		self.subroutines = sub
	def spawn_subroutines(self):
		for y in range(self.board_h):
			for x in range(self.board_w):
				i = self.instructions[y][x]
				if i and i[0] == 'S':
					self.subroutines[y][x] = {'current':[],'output':[]}
					if self.state[y][x]>=len(boards):
						print "Tried to load board " + str(self.state[y][x]) + " beyond end of boards"
						exit(1)
					self.subroutines[y][x]['current'] = copy.deepcopy(boards[self.state[y][x]])
	def add_input(self,n):
		l = len(self.inputs)
		self.inputs.append(n)
		self.marbles[self.inputcoords[l][0]][self.inputcoords[l][1]] = n
		return len(self.inputs)==self.input_count
	def get_output(self):
		if len(self.outputs)>0:
			return self.outputs.pop(0)
		else:
			return None
	def populate_outputs(self):
		c = max(self.output_count,self.exit_count)
		for i in range(c):
			if self.output_count>i:
				o = self.marbles[self.outputcoords[i][0]][self.outputcoords[i][1]]
			else:
				o = None
			if self.exit_count>i:
				x = self.marbles[self.exitcoords[i][0]][self.exitcoords[i][1]]
			else:
				x = None
			if o != None or x != None:
				self.outputs.append(x if x != None else o)
		return len(self.outputs)
	def tick(self):
		mbl = self.marbles
		ins = self.instructions
		sta = self.state
		# new marble and state arrays
		nmb = [[None for x in range(self.board_w)] for y in range(self.board_h)]
		nst = [[sta[y][x] for x in range(self.board_w)] for y in range(self.board_h)]
		exit_now = False
		# print mbl
		# process each marble
		for y in range(self.board_h):
			for x in range(self.board_w):
				def put(y,x,m):
					nmb[y][x] = m if not nmb[y][x] else (nmb[y][x]+m)%256
				m = mbl[y][x]
				i = ins[y][x]
				s = sta[y][x]
				l = 0 # move left?
				r = 0 # move right?
				d = 0 # move down?
				new_x = None
				new_y = None
				# print str(m) + "|" + str(y) + " " + str(x)
				if self.subroutines[y][x] and self.subroutines[y][x]['output']:
					o = self.subroutines[y][x]['output'][0].get_output()
					if o != None:
						put(y+1,x,o)
					else:
						self.subroutines[y][x]['output'].pop(0)
				if m == None: # no marble
					continue
				# print "considering " + print_cell(m) + " at " + str(y) + " " + str(x)
				if i: # instruction
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
						m += 1
					elif i == '--': # decrement
						d = 1
						m -= 1
					elif i[0] == '=': # equals state or constant?
						if i[1] != '?':
							s = int(i[1],36)
						if m == s:
							r = 1
						else:
							d = 1
					elif i[0] == '>': # greater than state or constant?
						if i[1] != '?':
							s = int(i[1],36)
						if m > s:
							r = 1
						else:
							d = 1
					elif i[0] == '<': # less than state or constant?
						if i[1] != '?':
							s = int(i[1],36)
						if m < s:
							r = 1
						else:
							d = 1
					elif i[0] == 'R': # random number, 0-static or 0-state inclusive
						if i[1] != '?':
							s = int(i[1],36)
						m = random.randint(0,s)
						d = 1
					elif i[0] == 'T': # teleporter
						if i[1] != '?':
							s = int(i[1],36)
						other_portals = []
						for k in range(self.board_h):
							for j in range(self.board_w):
								if (k!=y or j!=x) and \
									ins[k][j] and \
									ins[k][j][0] == 'T' and \
									sta[k][j] == s:
									other_portals.append((k,j))
						if other_portals:
							new_y,new_x=random.choice(other_portals)
							d = 1
						else:
							r = 1
					elif i[0] == 'P' and m != None: # pause
						if i[1] != 'N':
							s = int(i[1],36)
						# print "pause " + str(s) + " at " + str(y) + " " + str(x) + "?"
						d = 1
						for k in range(self.board_h):
							for j in range(self.board_w):
								# print x,y,m,k,j,ins[k][j],sta[k][j],mbl[k][j]
								if (k!=y or j!=x) and \
									ins[k][j] and \
									ins[k][j][0] == 'P' and \
									sta[k][j] == s and \
									mbl[k][j] == None:
									# print "nothing at " + str(k) + " " + str(j)
									d = 0
						if d == 0:
							put(y,x,m)
						# else:
							# print "unpause!"
					elif i[0] == 'S': # subroutine
						f=self.subroutines[y][x]['current']
						f.add_input(m)
						if len(f.inputs) == f.input_count:
							t = 0
							print "tick: " + str(t)
							f.display()
							f.spawn_subroutines()
							while f.tick():
								t += 1
								print "tick: " + str(t)
								f.display()
							d = 1
							f.populate_outputs()
							m = f.get_output()
							self.print_out += f.print_out
							if m != None:
								self.subroutines[y][x]['output'].append(f)
							self.subroutines[y][x]['current'] = copy.deepcopy(boards[self.state[y][x]])
					elif i[0] == 'O': # output
						put(y,x,m)
					elif i[0] == 'X': # exit
						put(y,x,m)
						exit_now = True
					else: # unrecognized instruction or Input
						d = 1

				else: # no instruction
					d = 1
				new_y = new_y if new_y!=None else y
				new_x = new_x if new_x!=None else x
				if d:
					if new_y==self.board_h-1:
						self.print_out += hex(m)[2:].zfill(2) + '(' + chr(m) + ') '
					else:
						put(new_y+1,new_x,m)
				if r:
					if new_x < self.board_w-1:
						if ins[new_y][new_x+1] and ins[new_y][new_x+1][0] in stateful_instructions:
							print "X"
							nst[new_y][new_x+1] = m
							if ins[new_y][new_x+1][0] == 'S':
								self.subroutines[new-y][new_x+1]['current'] = copy.deepcopy(boards[m])
						else:
							put(new_y,new_x+1,m)
				if l:
					if x > 0:
						put(y,x-1,m)
		diff = sum([cmp(x,y)!=0 for x,y in zip(self.marbles,nmb)])
		if diff == 0:
			return False
		if exit_now:
			# print "BAILING OUT!"
			return False
		self.marbles = nmb
		self.state = nst
		return True


# the boards array contains pristine instances of boards from the source
boards = []

#TODO: handle named functions
#TODO: handle ephemeral function states
with open(mblfile) as f:
	thisboard = Board()
	lines = []
	for line in f.readlines():
		if line != '\n':
			lines.append(line)
		else:
			thisboard.parse(lines)
			boards.append(thisboard)
			thisboard = Board()
			lines = []
	thisboard.parse(lines)
	boards.append(thisboard)

# make a copy of board zero as the main board
board = copy.deepcopy(boards[0])

if len(sys.argv)-2 != board.input_count:
	print sys.argv[1] + " expects " + str(board.input_count) + " inputs, you gave " + str(len(sys.argv)-2)
	exit(1)

board.spawn_subroutines()

for i in range(2,len(sys.argv)):
	board.add_input(int(sys.argv[i]))

t = 0
print "tick: " + str(t)
board.display()

#TODO: run until finished
while board.tick():
	# board.tick()
	t += 1
	print "tick: " + str(t)
	board.display()
print board.print_out
if board.output_count:
	board.populate_outputs()
	o = board.get_output()
	print str(o) + '(' + chr(o) + ') '
