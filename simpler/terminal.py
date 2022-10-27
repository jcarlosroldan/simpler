def getch():
	''' Reads a single byte from the user input. '''
	from os import name
	if name == 'nt':  # Windows-based systems
		from msvcrt import getch as ms_getch
		res = ms_getch()
	else:  # POSIX-based systems
		from tty import setcbreak
		from sys import stdin
		from termios import tcgetattr, tcsetattr, TCSADRAIN
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

def register_protocol_handler(protocol: str, path: str, link_name: str = None, content_type: str = None) -> None:
	''' Register a protocol handler in Windows, so that <protocol>:<address> links
	call command <path> <address>. I.e, `register_protocol_handler('magnet',
	'C:/Program Files/qBittorrent/qbittorrent.exe', link_name='URL:Magnet link',
	content_type='application/x-magnet')`. '''
	from os import name as os_name
	from elevate import elevate
	elevate()
	if os_name == 'nt':
		assert path not in ('explorer', 'explorer.exe', 'start', 'start.exe'), 'Setting start or explorer as a protocol handler would cause an infinite loop'
		from winreg import CreateKey, SetValue, SetValueEx, HKEY_CLASSES_ROOT, REG_SZ
		path = path.replace('/', '\\')
		key = CreateKey(HKEY_CLASSES_ROOT, protocol)
		if link_name is not None:
			SetValue(key, None, REG_SZ, link_name)
		if content_type is not None:
			SetValueEx(key, 'Content Type', 0, REG_SZ, content_type)
		SetValueEx(key, 'URL Protocol', 0, REG_SZ, '')
		SetValue(CreateKey(key, 'DefaultIcon'), None, REG_SZ, '"%s",1' % path)
		SetValue(CreateKey(key, 'shell'), None, REG_SZ, 'open')
		SetValue(CreateKey(key, 'shell\\open\\command'), None, REG_SZ, '"%s" "%%1"' % path)
	else:
		raise NotImplementedError('register_protocol_handler() is not implemented for your OS.')