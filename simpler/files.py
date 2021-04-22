from filecmp import cmp
from hashlib import md5
from json import load as jload, dump as jdump, dumps as jdumps
from os import listdir, makedirs, chdir, rename
from os.path import isdir, islink, join, exists
from pickle import load as pload, dump as pdump
from pandas.core.frame import DataFrame
from regex import compile
from pandas import read_csv, read_table
from time import time
from sys import path as sys_path

REGEX_FIND_EPISODE = compile(r'(?P<SEASON>\d+)\s*[x\-]\s*(?P<EPISODE>\d+)|S\s*(?P<SEASON>\d+)\s*E\s*(?P<EPISODE>\d+)|(?P<EPISODE>\d+)').search

def cwd():
	''' Change the base of relative paths to the directory of the main script. '''
	chdir(sys_path[0])

def load(path: str, format: str = 'auto', encoding: str = 'utf-8') -> object:
	''' Load a file in a given format. '''
	format = _detect_format(path, format)
	if format == 'string':
		fp = open(path, 'r', encoding=encoding)
	else:
		fp = open(path, 'rb')
	if format in ('bytes', 'string'):
		res = fp.read()
	elif format == 'json':
		res = jload(fp)
	elif format == 'jsonl':
		res = [jload(line) for line in fp]
	elif format == 'csv':
		res = read_csv(fp)
	elif format == 'table':
		res = read_table(fp)
	elif format == 'pickle':
		res = pload(fp)
	fp.close()
	return res

def save(path: str, content: object, format: str = 'auto', encoding: str = 'utf-8', append: bool = False, json_ensure_ascii=False, json_indent='\t', json_separators=(', ', ': '), pickle_protocol=4) -> None:
	''' Saves a file to the given format. '''
	format = _detect_format(path, format)
	if format in ('string', 'json', 'jsonl'):
		fp = open(path, 'a' if append else 'w', encoding=encoding)
	else:
		fp = open(path, 'ab' if append else 'wb')
	if format in ('bytes', 'string'):
		fp.write(content)
	elif format == 'json':
		fp.write(
			jdumps(content, ensure_ascii=json_ensure_ascii, indent=json_indent, separators=json_separators)
		)
	elif format == 'jsonl':
		fp.write(
			jdumps(elem, ensure_ascii=json_ensure_ascii, indent=json_indent, separators=json_separators)
			for elem in content
		)
	elif format == 'pickle':
		pdump(content, fp, protocol=pickle_protocol)
	elif format == 'csv':
		DataFrame(content).to_csv(path, index=False)
	elif format == 'table':
		DataFrame(content).to_excel(path, index=False)
	fp.close()

_accepted_formats = {
	'auto': (),
	'bytes': ('bin', 'db', 'dat', 'blob', 'bytes'),
	'csv': ('csv'),
	'json': ('json', 'js'),
	'jsonl': ('jsonl', 'jsl'),
	'pickle': ('pickle', 'pk', 'pkl', 'pck', 'pcl'),
	'string': ('txt', 'text', 'str'),
	'table': ('xlsx', 'odf', 'ods', 'odt', 'xls', 'xlsb', 'xlsm')
}

def _detect_format(path: str, format: str) -> str:
	if format == 'auto':
		if '.' in path:
			ext = path.rsplit('.', 1)[-1]
			for ext_format, exts in _accepted_formats.items():
				if ext in exts:
					format = ext_format
					break
		if format == 'auto':
			format = 'string'
	else:
		assert format in _accepted_formats, 'Unknown format %s. Accepted formats are: %s' % (
			format,
			', '.join(_accepted_formats.keys())
		)
	return format

def disk_cache(func=None, *, seconds: float = None, directory: str = '.cached/', identifier: str = None):
	''' The first time the decorated method is called, its result is stored as a pickle file, the
	next call loads the cached result from the disk. The cached files are used indefinitely unless the
	`seconds` lifespan is defined. The cached files are stored at `.cached` unless otherwise
	specificed with the `directory` argument. The cache file identifier is generated from the
	method name its arguments unless otherwise specified with the `identifier` argument. '''
	def decorator(func):
		def wrapper(*args, **kwargs):
			makedirs(directory, exist_ok=True)
			# compute the cached file identifier
			if identifier is None:
				fname = '%s|%s|%s' % (
					func.__name__,
					','.join(map(str, args)),
					','.join(map(lambda it: '%s:%s' % it, kwargs.items()))
				)
				fname = md5(fname.encode()).hexdigest()
			else:
				fname = identifier
			fname = join(directory, str(fname))
			# return the value, cached or not
			res = None
			now = time()
			if exists(fname):
				with open(fname, 'rb') as fp:
					save_time, value = pload(fp)
				if seconds is None or save_time - now < seconds:
					res = value
			if res is None:
				res = func(*args, **kwargs)
				with open(fname, 'wb') as fp:
					pdump((now, res), fp)
			return res
		return wrapper
	if func:
		return decorator(func)
	else:
		return decorator

def size(file):
	''' A way to see the size of a file without loading it to memory. '''
	if file.content_length:
		return file.content_length
	try:
		pos = file.tell()
		file.seek(0, 2)
		size = file.tell()
		file.seek(pos)
		return size
	except (AttributeError, IOError):
		pass
	return 0

_find_hidden_compressed_signatures = {
	'RNC': b'\x52\x4e\x43\x01',
	'RNC2': b'\x52\x4e\x43\x02',
	'lzip': b'\x4c\x5a\x49\x50',
	'zip': b'\x50\x4b\x03\x04',
	'zip-spanned': b'\x50\x4b\x07\x08',
	'rar1.5+': b'\x52\x61\x72\x21\x1a\x07\x00',
	'rar5.0+': b'\x52\x61\x72\x21\x1a\x07\x01\x00',
	'iso': b'\x43\x44\x30\x30\x31',
	'xar': b'\x78\x61\x72\x21',
	'tar1': b'\x75\x73\x74\x61\x72\x00\x30\x30',
	'tar2': b'\x75\x73\x74\x61\x72\x20\x20\x00',
	'7z': b'\x37\x7a\xbc\xaf\x27\x1c',
	'lz4': b'\x04\x22\x4d\x18',
	'webm': b'\x1a\x45\xdf\xa3',
	'xz': b'\xfd\x37\x7a\x58\x5a\x00',
	'wim': b'\x4d\x53\x57\x49\x4d\x00\x00',
	# signatures with too many false positives below
	# 'pdf': b'\x25\x50\x44\x46',
	# 'zip-empty': b'\x50\x4b\x05\x06',
	# 'gz': b'\x1f\x8b\x08',
	# 'tar': b'\x1f\x9d',
	# 'bz2': b'\x42\x5a\x68',
}
def find_hidden_compressed(path):
	with open(path, 'rb') as fp:
		data = fp.read()
		signatures = []
		for ftype, signature in _find_hidden_compressed_signatures.items():
			if data.find(signature) != -1:
				signatures.append(ftype)
		return signatures

def tvshow_rename(path):
	''' Rename every TV show of a folder.
	E.g. Inception_Season_4_Episode_02_DivX-Total.mkv would be 04x02.mkv. '''
	for file in listdir(path):
		name, ext = file.rsplit('.', 1)
		match = REGEX_FIND_EPISODE(name.replace('_', ' '))
		if match is not None:
			season, episode = match.groups()
			season = 1 if season is None else int(season)
			episode = int(episode)
			name = '%02d x %02d.%s' % (season, episode, ext)
			rename(file, name)

_directory_compare_ignored = ('.class', '.metadata', '.recommenders', '.pyc', '.git', '.svn', '.cached', '__pycache__')
def directory_compare(old, new, kind='dir', ignored=_directory_compare_ignored):
	def children(path):
		res = {}
		for child in listdir(path):
			if not any(child.endswith(ext) for ext in ignored):
				full = join(path, child)
				is_dir = 'dir' if isdir(full) else 'file'
				if not islink(full):  # symbolic links are ignored in the comparison
					res[(is_dir, child)] = full
		return res
	if kind == 'file':
		if not cmp(old, new, shallow=False):
			print('Modified\tfile\t%s' % new)
	else:
		old_childs, new_childs = children(old), children(new)
		for child in old_childs:
			if child not in new_childs:
				print('Deleted \t%s\t%s' % (child[0], old_childs[child]))
		for child in new_childs:
			if child not in old_childs:
				print('Created \t%s\t%s' % (child[0], new_childs[child]))
			else:
				directory_compare(old_childs[child], new_childs[child], child[0])