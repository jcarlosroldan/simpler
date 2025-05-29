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
	''' Given a past date, it returns a date in a human-friendly format "1 month ago". '''
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

def print_matrix(matrix: list, rows: int = None, cols: int = None, elem_width: int = None, separator: str = ' ') -> None:
	for row in matrix[:rows]:
		for col in row[:cols]:
			print(str(col)[:elem_width], end=separator)
		print()

_safe_filename_windows_reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{prefix}{i}' for prefix in ['COM', 'LPT'] for i in range(1, 10)}
def safe_filename(
	filename: str,
	trim_spaces: bool = True,
	disallowed_chars: set = set('/\\*;[]":=,<>'),
	length_limit: int = None,
	suffix_windows_reserved_names: bool = False
) -> str:
	''' Returns a safe filename by removing disallowed characters, trimming spaces, and optionally
	adding a suffix to Windows reserved names. If `length_limit` is set, it will truncate the filename
	to that length, removing trailing spaces and dots. '''
	res = ''.join(char for char in filename if char not in disallowed_chars)
	if trim_spaces: res = res.strip(' ')
	if suffix_windows_reserved_names and res.upper() in _safe_filename_windows_reserved: res = f'{res}_safe'
	if length_limit and len(res) > length_limit: res = res[:length_limit].rstrip(' .')
	return res