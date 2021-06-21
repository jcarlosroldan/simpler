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

_cprint_palette = {
	'default': 39, 'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34,
	'magenta': 35, 'cyan': 36, 'light_gray': 37, 'dark_gray': 90, 'light_red': 91,
	'light_green': 92, 'light_yellow': 93, 'light_blue': 94, 'light_magenta': 95,
	'light_cyan': 96, 'white': 97
}
def cprint(*args: tuple, fg='default', bg='default', **kwargs):
	''' Same syntax as print, with two optional parameters `fg` and `bg` to change
	the print color. Available colors are: default, black, red, green, yellow, blue,
	magenta, cyan, light_gray, dark_gray, light_red, light_green, light_yellow, light_blue,
	light_magenta, light_cyan, and white. '''
	print('\033[%dm\033[%dm%s\033[0m' % (
		_cprint_palette[fg],
		_cprint_palette[bg] + 10,
		' '.join(args)),
		**kwargs
	)