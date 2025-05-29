from typing import Union


def assert_set(data: dict, name: str, optional: bool = False, default: object = None):
	''' Asserts that data[name] exists and returns it. '''
	if optional and name not in data: return default
	assert name in data, '%s is not set.' % name
	return data[name]

def assert_str(
	data: dict, name: str, optional: bool = False, min_len: int = None,
	max_len: int = None, has_letter: bool = None, has_number: bool = None,
	has_symbol: bool = None, has_whitespace: bool = None, has_pattern: str = None,
	default: object = None
) -> str:
	''' Asserts all the requested checks to data[name] and returns it. '''
	from re import search
	if optional and name not in data: return default
	assert_set(data, name)
	assert isinstance(data[name], str), '%s must be a string.' % name
	if min_len is not None:
		assert len(data[name]) >= min_len, '%s should be %d characters at least.' % (name, min_len)
	if max_len is not None:
		assert len(data[name]) <= max_len, '%s should be %d characters at most.' % (name, max_len)
	if has_letter is not None:
		contains = search(r'[a-z]', data[name].lower()) is not None
		if has_letter:
			assert contains, '%s must contain at least one letter.' % name
		else:
			assert not contains, '%s must not contain letters.' % name
	if has_number is not None:
		contains = search(r'\d', data[name]) is not None
		if has_number:
			assert contains, '%s must contain at least one number.' % name
		else:
			assert not contains, '%s must not contain any numbers.' % name
	if has_symbol is not None:
		contains = search(r'[^\w\s]', data[name]) is not None
		if has_symbol:
			assert contains, '%s must contain at least one symbol.' % name
		else:
			assert not contains, '%s must not contain any symbols.' % name
	if has_whitespace is not None:
		contains = search(r'\s', data[name]) is not None
		if has_whitespace:
			assert contains, '%s must contain at least one whitespace.' % name
		else:
			assert not contains, '%s must not contain any whitespaces.' % name
	if has_pattern is not None:
		assert search('^(%s)$' % has_pattern, data[name]) is not None, '%s has an invalid format.' % name
	return data[name]

def assert_number(
	data: dict, name: str, optional: bool = False, min_val: int = None,
	max_val: int = None, is_integer: bool = None, default: object = None
) -> Union[int, float]:
	''' Asserts all the requested numeric checks to data[name] and returns it. '''
	if optional and name not in data: return default
	assert_set(data, name)
	try:
		val = float(data[name])
	except ValueError:
		raise AssertionError('%s must be a number.' % name)
	if is_integer is True:
		assert val.is_integer(), '%s must be an integer.' % name
		val = int(val)
	elif is_integer is False:
		assert not val.is_integer(), '%s must not be an integer.' % name
	if min_val is not None:
		assert val >= min_val, '%s must be %s at least.' % (name, min_val)
	if max_val is not None:
		assert val <= max_val, '%s must be %s at most.' % (name, max_val)
	return val

def assert_id(
	data: dict, name: str, optional: bool = False, allow_zero: bool = False,
	default: object = None
) -> int:
	''' Asserts that data[name] is a valid database id and returns it. '''
	return assert_number(
		data,
		name,
		min_val=0 if allow_zero else 1,
		optional=optional,
		default=default,
		is_integer=True
	)

def assert_mail(data: dict, name: str, optional: bool = False, default: object = None) -> str:
	''' Asserts that data[name] is a valid mail string and returns it. '''
	from re import match
	if optional and name not in data: return default
	assert_set(data, name)
	assert match(r'[^\s@]+@[^\s@]+\.[^\s@]+', data[name]), '%s is not a valid mail.' % name
	return data[name]

def assert_exists(path: str) -> None:
	''' Asserts that the given path exists within PATH_STATIC. '''
	from os.path import exists
	assert exists(path), 'Non-existing resource "%s".' % path