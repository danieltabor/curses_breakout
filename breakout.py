#!/usr/bin/env python3
## Copyright (c) 2022 Daniel Tabor
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions
## are met:
## 1. Redistributions of source code must retain the above copyright
##    notice, this list of conditions and the following disclaimer.
## 2. Redistributions in binary form must reproduce the above copyright
##    notice, this list of conditions and the following disclaimer in the
##    documentation and/or other materials provided with the distribution.
##
## THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS "AS IS" AND
## ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
## ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
## FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
## LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
## OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
## SUCH DAMAGE.
##
import sys
import time
import random
import traceback

try:
	import curses
except ImportError:
	print("This program requires curses.")
	sys.exit(0)

PADDLE_WIDTH = 0.20
BRICK_WIDTH = 0.10
KEY_ESC = 27
KEY_q = ord("q")
KEY_p = ord("p")
KEY_LEFT = ord(",")
KEY_RIGHT = ord(".")
KEY_SPACE = ord(" ")

class Sprite:
	def __init__(self,text,color,y=0,x=0):
		self.x = x
		self.y = y
		self.text = [[c for c in line] for line in text.split("\n")]
		self.h = len(self.text)
		self.w = len(self.text[0])
		self.color = color

	def move(self,y,x):
		if self.y != y or self.x != x:
			self.clear()
		self.y = y
		self.x = x

	def clear(self):
		intx = int(round(self.x))
		inty = int(round(self.y))
		scr.attroff(curses.A_BOLD)
		scr.attron(curses.color_pair(1))
		[[scr.addch(inty+y,intx+x," ") for x in range(self.w) if intx+x>=0 and intx+x<scrw] for y in range(self.h) if inty+y>=0 and inty+y<scrh]

	def _set_color(self,y=None):
		if self.color[0]:
			scr.attron(curses.A_BOLD)
		else:
			scr.attroff(curses.A_BOLD)
		scr.attron(curses.color_pair(self.color[1]))
		
	
	def draw(self):
		intx = int(round(self.x))
		inty = int(round(self.y))
		for y in range(self.h):
			scry = inty+y
			if scry < 0:
				continue
			elif scry >= scrh:
				break
			self._set_color(y)
			try:
				[scr.addch(scry,intx+x,self.text[y][x]) for x in range(self.w) if intx+x>=0 and intx+x<scrw]
			except:
				pass

class Paddle(Sprite):
	def __init__(self):
		width = int(PADDLE_WIDTH*scrw)
		text = "="*int(width)
		Sprite.__init__(self,text,(True,1),scrh-2,int((scrw-width)/2))

	def move(self,x):
		##The following code adds end stops to the paddle
		#if x<0:
		#	x = 0
		#if x+self.w >= scrw:
		#	x = scrw-self.w
		Sprite.move(self,scrh-2,x)

class Ball(Sprite):
	def __init__(self):
		Sprite.__init__(self,"O",(True,1),scrh/2,scrw/2)
		self.vel_x = 0
		self.vel_y = 0
		self.lastx = self.x
		self.lasty = self.y
	
	def ready_to_spawn(self):
		if self.vel_x == 0 and self.vel_y == 0:
			return True

	def reset(self):
		self.clear()
		self.y = scrh/2
		self.x = scrw/2
		self.vel_x = 0
		self.vel_y = 0

	def spawn(self):
		self.vel_y = 0.1
		self.vel_x = float(random.randint(0,1)-2)/100.0

	def move(self):
		global paddle
		global bricks
		ret_score = False
		ret_died = False
		intx = int(round(self.x))
		inty = int(round(self.y))


		if bricks.collision(inty,intx):
			diffx = abs(self.lastx-self.x)
			diffy = abs(self.lasty-self.y)
			if diffx == diffy:
				self.vel_y = -1*(self.vel_y+0.01)
				self.vel_x = -1*(self.vel_x+0.01)
			elif diffx > diffy:
				self.vel_x = -1*(self.vel_x+0.01)
			else:
				self.vel_y = -1*(self.vel_y+0.01)
			ret_score = True
		self.lastx = self.x
		self.lasty = self.y

		if intx == 0 or intx == scrw-1:
			self.vel_x = -1*self.vel_x
		if inty == 0:
			self.vel_y = -1*self.vel_y
		elif inty == scrh-2 and \
				intx >= paddle.x and \
				intx < paddle.x+paddle.w:
			self.vel_y = -1*(self.vel_y+0.01)
			if self.vel_y < -1:
				self.vel_y = -1
			xper = -2*(float(self.x-paddle.x)/paddle.w - 0.5)
			self.vel_x = xper*self.vel_y
		elif inty == scrh:
			self.reset()
			ret_died = True

		if self.vel_x > 1:
			self.vel_x = 1
			self.x = intx
		elif self.vel_x < -1:
			self.vel_x = -1
			self.x = intx
		if self.vel_y > 1:
			self.vel_y = 1
			self.y = inty
		elif self.vel_y < -1:
			self.vel_y = -1
			self.y = inty
		Sprite.move(self,self.y+self.vel_y,self.x+self.vel_x)
		return ret_score,ret_died

class Bricks(Sprite):
	def __init__(self):
		text = "\n".join(["".join(["@" for x in range(scrw-6)]) for y in range(int(scrh*0.20))])
		self.count = sum([1 for c in text if c == "@"])
		Sprite.__init__(self,text,(None,None),int(scrh*0.20),3)
		self.colors = [2,3,4,5]

	def collision(self,y,x):
		if y>= self.y and y<self.y+self.h and x>=self.x and x<self.x+self.w:
			if self.text[y-self.y][x-self.x] == "@":
				self.text[y-self.y][x-self.x] = " "
				self.count = self.count - 1
				return True
		else:
			return False

	def get_count(self):
		return self.count

	def _set_color(self,y=None):
		if y == None:
			y = 0
		bold = 1-((int(y)/int(len(self.colors)))%2)
		color = self.colors[y%len(self.colors)]
		if bold:
			scr.attron(curses.A_BOLD)
		else:
			scr.attroff(curses.A_BOLD)
		scr.attron(curses.color_pair(color))
	

def draw_frame():
	global score
	global ball_count
	scr.attroff(curses.A_BOLD)
	scr.attron(curses.color_pair(1))
	[[scr.addch(y,0,"#"),scr.addch(y,scrw-1,"#")] for y in range(scrh-2)]
	[scr.addch(0,x,"#") for x in range(scrw)]
	scr.addstr(scrh-1,2,"Score: %4s" % str(score))
	scr.addstr(scrh-1,scrw-10,"Balls: %d" % ball_count)


def reset():
	global score
	global ball_count
	global bricks
	global ball
	score = 0
	ball_count = 5
	bricks = Bricks()
	ball.reset()

def dialog(text,color):
	x = int((scrw-len(text[0]))/2)
	y = int((scrh-len(text))/2)
	if color[0]:
		scr.attron(curses.A_BOLD)
	else:
		scr.attroff(curses.A_BOLD)
	scr.attron(curses.color_pair(color[1]))
	[ scr.addstr(y+i,x,text[i]) for i in range(len(text))]
	scr.refresh()
	while True:
		input = scr.getch()
		if input == KEY_SPACE:
			break
		if input == KEY_q:
			curses.endwin()
			sys.exit(0)
		time.sleep(0.010)
	[[scr.addch(y+i,x+j," ") for j in range(len(text[0]))] for i in range(len(text))]
	scr.attroff(curses.A_BOLD)
	scr.attron(curses.color_pair(1))
	[[scr.addch(y+i,x+j," ") for j in range(len(text[i]))] for i in range(len(text))]
	

welcome=["+--------------------------------------------+",
	 "|                 Breakout                   |",
	 "| (Isn't there something I should be doing?) |",
	 "+--------------------------------------------+",
 	 "| Controls:                                  |",
	 "| [Space] to start                           |",
	 "| [<] to move paddle left                    |",
	 "| [>] to move paddle right                   |",
	 "| [p] to pause                               |",
	 "| [q] to quit                                |",
	 "+--------------------------------------------+",
	 "| Copyright George P. Burdell                |",
         "|   All contents are proprietary and no      |",
	 "|   license is granted to anyone to play,    |",
	 "|   observe, or otherwise enjoy this work.   |",
	 "+--------------------------------------------+"]
gameover=["+-------------------------------------------+",
	  "|               GAME OVER                   |",
	  "+-------------------------------------------+",
	  "| Your final score was:                     |",
	  "|   %38s  |",
	  "|                                           |",
	  "| But is there anyone to brag to... really? |",
	  "|                                           |",
	  "| [Space] to restart                        |",
          "+-------------------------------------------+"]
pause=[ "+-------------------------------------------+",
	"|                 PAUSE                     |",
	"+-------------------------------------------+",
	"| Your game is paused. This is a good       |",
	"| idea, goofing off can be so stressful.    |",
	"|                                           |",
	"| [Space] to unpause                        |",
	"+-------------------------------------------+"]

def main():
	global scr
	global scrw
	global scrh
	global bricks
	global paddle
	global score
	global ball_count
	global ball

	try:
		scr = curses.initscr()
		scrh, scrw = scr.getmaxyx()
		curses.noecho()
		curses.nocbreak()
		scr.keypad(True)
		scr.nodelay(True)
		curses.start_color()
		curses.init_pair(1,curses.COLOR_WHITE,curses.COLOR_BLACK)
		curses.init_pair(2,curses.COLOR_BLUE,curses.COLOR_BLACK)
		curses.init_pair(3,curses.COLOR_RED,curses.COLOR_BLACK)
		curses.init_pair(4,curses.COLOR_GREEN,curses.COLOR_BLACK)
		curses.init_pair(5,curses.COLOR_YELLOW,curses.COLOR_BLACK)
		curses.init_pair(6,curses.COLOR_WHITE,curses.COLOR_BLUE)
		curses.init_pair(7,curses.COLOR_WHITE,curses.COLOR_RED)

		try:
			dialog(welcome,(True,6))
		except SystemExit:
			curses.endwin()
			sys.exit(0)
		except:
			curses.endwin()
			print("Basic Rendering is not working.  You terminal may be too small.")
			sys.exit(0)

		paddle = Paddle()
		ball = Ball()
		reset()

		while True:
			input = scr.getch()
			if input == KEY_LEFT:
				paddle.move(paddle.x-1)
			elif input == KEY_RIGHT:
				paddle.move(paddle.x+1)
			elif input == KEY_SPACE and ball.ready_to_spawn():
				ball.spawn()
			elif input == KEY_p:
				dialog(pause,(False,6))
			elif input in [KEY_ESC,KEY_q]:
				break
			frame_score, frame_died = ball.move()
			if frame_score:
				score = score + 1
			if frame_died:
				ball_count = ball_count - 1
			if ball_count == -1 or bricks.get_count() == 0:
					dialog(gameover[:4]+[gameover[4]%score] + gameover[5:],(True,7))
					reset()
			draw_frame()
			paddle.draw()
			bricks.draw()
			ball.draw()
			scr.move(scrh-1,scrw-1)
			scr.refresh()
			time.sleep(0.010)
		curses.endwin()
	except SystemExit:
		curses.endwin()
	except:
		curses.endwin()
		traceback.print_exc()

if __name__ == "__main__":
	main()

