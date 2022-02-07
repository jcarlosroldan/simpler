def human_bytes(size: float, decimal_places: int = 2) -> str:
	''' Returns a human readable file size from a number of bytes. '''
	for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']:
		if size < 1024: break
		size /= 1024
	return f'{size:.{decimal_places}f}{unit}B'

def human_seconds(seconds: float) -> str:
	''' Returns a human readable string from a number of seconds. '''
	from datetime import timedelta
	return str(timedelta(seconds=int(seconds))).zfill(8)

_human_date_measures = (
	('year', 365 * 24 * 3600),
	('month', 30 * 24 * 3600),
	('week', 7 * 24 * 3600),
	('day', 24 * 3600),
	('hour', 3600),
	('minute', 60),
	('second', 1)
)
def human_date(date) -> str:
	''' Return a date the a human-friendly format "1 month ago". '''
	from datetime import datetime
	if isinstance(date, str):
		res = datetime.strptime(date, '%Y-%m-%d, %H:%M:%S')
	else:
		res = date
	diff = (datetime.now() - res).total_seconds()
	if diff < 1:
		return 'just now'
	else:
		for name, amount in _human_date_measures:
			if diff > amount:
				diff = diff // amount
				return '%d %s%s ago' % (diff, name, 's' if diff > 1 else '')

def random_string(length: int, mask: list = None) -> str:
	''' Returns a random string. '''
	from random import choice
	if mask is None:
		from string import digits, ascii_letters
		mask = digits + ascii_letters
	return ''.join(choice(mask) for _ in range(length))

def print_matrix(matrix: list, rows: int = None, cols: int = None, elem_width: int = None, separator: str = ' ') -> str:
	for row in matrix[:rows]:
		for col in row[:cols]:
			print(str(col)[:elem_width], end=separator)
		print()

_safe_filename_regex = None
def safe_filename(filename: str) -> str:
	global _safe_filename_regex
	if _safe_filename_regex is None:
		from regex import compile
		_safe_filename_regex = compile(r'[/\\\*;\[\]\":=,<>]')
	return _safe_filename_regex.sub('', filename)