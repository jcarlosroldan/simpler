from os import name
if name == 'nt':  # Windows-based systems
	from msvcrt import getch as ms_getch
else:  # POSIX-based systems
	from tty import setcbreak
	from sys import stdin
	from termios import tcgetattr, tcsetattr, TCSADRAIN

def getch():
	''' Reads a single byte from the user input. '''
	if name == 'nt':
		res = ms_getch()
	else:
		fd = stdin.fileno()
		oldSettings = tcgetattr(fd)
		try:
			setcbreak(fd)
			res = stdin.read(1)
		finally:
			tcsetattr(fd, TCSADRAIN, oldSettings)
	return res