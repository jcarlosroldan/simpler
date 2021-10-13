from filecmp import cmp
from hashlib import md5
from json import load as jload, dumps as jdumps
from os import listdir, makedirs, chdir, rename
from os.path import isdir, islink, join, exists, abspath, dirname
from pickle import load as pload, dump as pdump
from typing import Optional
from regex import compile
from time import time
from sys import path as sys_path
from collections import OrderedDict
from os import makedirs
from shutil import copyfileobj

REGEX_FIND_EPISODE = compile(r'(?P<SEASON>\d+)\s*[x\-]\s*(?P<EPISODE>\d+)|S\s*(?P<SEASON>\d+)\s*E\s*(?P<EPISODE>\d+)|(?P<EPISODE>\d+)').search

def cwd() -> None:
	''' Change the current directory to the base of relative paths to the directory
	and returns it. '''
	path = abspath(sys_path[0])
	chdir(path)
	return path

_load_formats = 'bytes', 'csv', 'json', 'jsonl', 'pickle', 'string', 'table', 'yaml'
def load(path: str, format: str = 'auto', encoding: str = 'utf-8', inner_args: list = None, inner_kwargs: dict = None) -> object:
	''' Load a file in a given format. '''
	format = detect_format(path, format, accept=_load_formats, default='string')
	args = [] if inner_args is None else inner_args
	kwargs = {} if inner_kwargs is None else inner_kwargs
	if format == 'string':
		fp = open(path, 'r', encoding=encoding)
	else:
		fp = open(path, 'rb')
	if format in ('bytes', 'string', 'jsonl'):
		res = fp.read()
	elif format == 'json':
		res = jload(fp, *args, **kwargs)
	elif format == 'jsonl':
		res = [jload(line, *args, **kwargs) for line in fp]
	elif format == 'csv':
		from pandas import read_csv
		res = read_csv(fp, *args, **kwargs)
	elif format == 'table':
		from pandas import read_table
		res = read_table(fp, *args, **kwargs)
	elif format == 'pickle':
		res = pload(fp, *args, **kwargs)
	elif format == 'yaml':
		from yaml import safe_load_all as yload
		res = list(yload(fp, *args, **kwargs))
		res = res[0] if len(res) == 1 else res
	fp.close()
	return res

def save(path: str, content: object, format: str = 'auto', encoding: str = 'utf-8', append: bool = False, inner_args: list = None, inner_kwargs: dict = None) -> None:
	''' Saves a file to the given format. '''
	format = detect_format(path, format, accept=_load_formats, default='string')
	args = [] if inner_args is None else inner_args
	kwargs = {} if inner_kwargs is None else inner_kwargs
	if format in ('string', 'json', 'jsonl', 'yaml'):
		fp = open(path, 'a' if append else 'w', encoding=encoding)
	elif format in ('bytes', 'pickle'):
		fp = open(path, 'ab' if append else 'wb')
	else:
		fp = None
	if format in ('bytes', 'string'):
		fp.write(content)
	elif format in ('json', 'jsonl'):
		if 'ensure_ascii' not in kwargs: kwargs['ensure_ascii'] = False
		if 'indent' not in kwargs: kwargs['indent'] = '\t'
		if format[-1] == 'l':
			fp.write(jdumps(elem, *args, **kwargs) for elem in content)
		else:
			fp.write(jdumps(content, *args, **kwargs))
	elif format == 'pickle':
		if 'protocol' not in kwargs: kwargs['protocol'] = 4
		pdump(content, fp, *args, **kwargs)
	elif format == 'csv':
		from pandas import DataFrame
		if 'index' not in kwargs: kwargs['index'] = False
		DataFrame(content).to_csv(path, *args, **kwargs)
	elif format == 'table':
		from pandas import DataFrame
		if 'index' not in kwargs: kwargs['index'] = False
		DataFrame(content).to_excel(path, *args, **kwargs)
	elif format == 'yaml':
		from yaml import dump as ydump
		ydump(content, fp, *args, **kwargs)
	if fp is not None:
		fp.close()

_decompress_formats = 'tar', 'zip', 'gzip', 'bzip2', 'rar', '7zip', 'lzma'
def decompress(input_file: str, output_dir: str = None, format: str = 'auto') -> None:
	''' Decompress the given file to the output directory regardless of its format. '''
	if output_dir is None:
		output_dir = dirname(input_file)
	else:
		makedirs(output_dir, exist_ok=True)
	format = detect_format(input_file, format, accept=_decompress_formats)
	if format == 'zip':
		from zipfile import ZipFile
		with ZipFile(input_file, 'r') as i:
			i.extractall(output_dir)
	elif format == 'gzip':
		from gzip import GzipFile
		o_dir = join(output_dir, input_file.rsplit('.', 1)[0])
		with GzipFile(input_file, 'r') as i, open(o_dir, 'wb') as o:
			copyfileobj(i, o)
	elif format == 'rar':
		from rarfile import RarFile
		with RarFile(input_file, 'r') as i:
			i.extractall(output_dir)
	elif format == 'bzip2':
		from bz2 import open as open_bz2
		with open_bz2(input_file, 'r') as i, open(output_dir, 'wb') as o:
			copyfileobj(i, o)
	elif format == 'tar':
		from tarfile import open as open_tar
		with open_tar(input_file) as i:
			i.extractall(output_dir)
	elif format == '7zip':
		from py7zr import SevenZipFile
		with SevenZipFile(input_file, 'r') as i:
			i.extractall(output_dir)
	elif format == 'lzma':
		from lzma import open as open_lzma, decompress as lzdecompress
		with open_lzma(input_file, 'r') as i, open(output_dir, 'wb') as o:
			copyfileobj(lzdecompress(i), o)

_detect_format_exts = OrderedDict((
	('bytes', ('bin', 'db', 'dat', 'blob', 'bytes')),
	('csv', ('csv',)),
	('json', ('json', 'js')),
	('jsonl', ('jsonl', 'jsl')),
	('pickle', ('pickle', 'pk', 'pkl', 'pck', 'pcl')),
	('string', ('txt', 'text', 'str')),
	('table', ('xlsx', 'odf', 'ods', 'odt', 'xls', 'xlsb', 'xlsm')),
	('yaml', ('yaml', 'yml')),
	('tar', ('tar', 'tar-linux32', 'tar-linux64', 'tar.gz')),
	('zip', ('zip', 'cbz')),
	('gzip', ('gz', 'gzip', 'gunzip')),
	('bzip2', ('bzip2', 'bz2')),
	('rar', ('rar', 'cbr')),
	('7zip', ('7z', '7zip')),
	('lzma', ('lzip', 'lz')),
))
def detect_format(path: str, format: str, accept: list = None, default: str = None) -> Optional[str]:
	''' Detects the format of a file from its path. '''
	if format == 'auto':
		name = path.lower()
		for ext_format, exts in _detect_format_exts.items():
			if any(name.endswith('.' + ext) for ext in exts):
				format = ext_format
				break
		else:
			format = default
	if accept is not None:
		assert format in accept, 'Unknown format for file at "%s". Accepted formats are %s.' % (
			path,
			', '.join(accept)
		)
	return format

def disk_cache(func=None, *, seconds: float = None, directory: str = '.cached/', identifier: str = None):
	''' The first time the decorated method is called, its result is stored as a pickle file, the
	next call loads the cached result from the disk. The cached files are used indefinitely unless the
	`seconds` lifespan is defined. The cached files are stored at `.cached` unless otherwise
	specificed with the `directory` argument. The cache file identifier is generated from the
	method name plus its arguments, unless otherwise specified with the `identifier` argument. '''
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

def size(file) -> int:
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
def find_hidden_compressed(path: str) -> list:
	''' Recursively examines the signature of the files in a directory while looking for a
	compressed file. '''
	with open(path, 'rb') as fp:
		data = fp.read()
		signatures = []
		for ftype, signature in _find_hidden_compressed_signatures.items():
			if data.find(signature) != -1:
				signatures.append(ftype)
		return signatures

def tvshow_rename(path: str) -> None:
	''' Rename every TV show of a folder.
	I.e. Inception_Season_4_Episode_02_DivX-Total.mkv would be 04x02.mkv. '''
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
def directory_compare(old: str, new: str, kind: str = 'dir', ignored: list = _directory_compare_ignored) -> None:
	''' Compares the files in two directories (old and new) to detect files that have been created,
	deleted, changed or updated, ignoring the specified files. '''
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