from typing import Callable, Optional

def cwd() -> None:
	from os.path import abspath
	from os import chdir
	from sys import path as sys_path
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
		from json import load as jload
		res = jload(fp, *args, **kwargs)
	elif format == 'jsonl':
		from json import load as jload
		res = [jload(line, *args, **kwargs) for line in fp]
	elif format == 'csv':
		from pandas import read_csv
		res = read_csv(fp, *args, **kwargs)
	elif format == 'table':
		from pandas import read_table
		res = read_table(fp, *args, **kwargs)
	elif format == 'pickle':
		from pickle import load as pload
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
		from json import dumps as jdumps
		if 'ensure_ascii' not in kwargs: kwargs['ensure_ascii'] = False
		if 'indent' not in kwargs: kwargs['indent'] = '\t'
		if format[-1] == 'l':
			fp.write(jdumps(elem, *args, **kwargs) for elem in content)
		else:
			fp.write(jdumps(content, *args, **kwargs))
	elif format == 'pickle':
		from pickle import dump as pdump
		if 'protocol' not in kwargs: kwargs['protocol'] = 4
		pdump(content, fp, *args, **kwargs)
	elif format == 'csv':
		from pandas import DataFrame
		if 'index' not in kwargs: kwargs['index'] = False
		if 'encoding' not in kwargs: kwargs['encoding'] = 'utf-8-sig'
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
		from os.path import dirname
		output_dir = dirname(input_file)
	else:
		from os import makedirs
		makedirs(output_dir, exist_ok=True)
	format = detect_format(input_file, format, accept=_decompress_formats)
	if format == 'zip':
		from zipfile import ZipFile
		with ZipFile(input_file, 'r') as i:
			i.extractall(output_dir)
	elif format == 'gzip':
		from gzip import GzipFile
		from os.path import join
		from shutil import copyfileobj
		o_dir = join(output_dir, input_file.rsplit('.', 1)[0])
		with GzipFile(input_file, 'r') as i, open(o_dir, 'wb') as o:
			copyfileobj(i, o)
	elif format == 'rar':
		from rarfile import RarFile
		with RarFile(input_file, 'r') as i:
			i.extractall(output_dir)
	elif format == 'bzip2':
		from bz2 import open as open_bz2
		from shutil import copyfileobj
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
		from shutil import copyfileobj
		with open_lzma(input_file, 'r') as i, open(output_dir, 'wb') as o:
			copyfileobj(lzdecompress(i), o)

_detect_format_exts = (
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
)
def detect_format(path: str, format: str, accept: list = None, default: str = None) -> Optional[str]:
	''' Detects the format of a file from its path. '''
	if format == 'auto':
		name = path.lower()
		for ext_format, exts in _detect_format_exts:
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

def disk_cache(method=None, *, seconds: float = None, directory: str = '.cached/', identifier: str = None):
	''' The first time the decorated method is called, its result is stored as a pickle file, the
	next call loads the cached result from the disk. The cached files are used indefinitely unless the
	`seconds` lifespan is defined. The cached files are stored at `.cached` unless otherwise
	specificed with the `directory` argument. The cache file identifier is generated from the
	method name plus its arguments, unless otherwise specified with the `identifier` argument. '''
	def decorator(method):
		def wrapper(*args, **kwargs):
			from hashlib import md5
			from os import makedirs
			from os.path import join, exists
			from time import time
			makedirs(directory, exist_ok=True)
			# compute the cached file identifier
			if identifier is None:
				fname = '%s|%s|%s' % (
					method.__name__,
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
				from pickle import load as pload
				with open(fname, 'rb') as fp:
					save_time, value = pload(fp)
				if seconds is None or save_time - now < seconds:
					res = value
			if res is None:
				from pickle import dump as pdump
				res = method(*args, **kwargs)
				with open(fname, 'wb') as fp:
					pdump((now, res), fp)
			return res
		return wrapper
	if method:
		return decorator(method)
	else:
		return decorator

_mem_cache_global = {}
def mem_cache(
	method=None, *, key: Callable = None, maxsize: int = None, is_global: bool = False,
	global_name: str = None
):
	''' Decorator to cache the output of a method. It is indexed by its arguments
	unless the `key` argument is specified, in which case `key(*args, **kwargs)`
	will be called to get the indexing key. If `maxsize` is defined, it is bounded
	as an LRU cache with `maxsize` elements at most. If `is_global` is defined,
	the cache will be stored globally, so that it can be shared accross multiple
	methods of multiple instances of a class. A `global_name` can be
	defined to identify the method; otherwise, the method name will be used. '''
	if key is None:
		key = lambda *args, **kwargs: frozenset(args + tuple(kwargs.items()))
	if method is None:
		return lambda method: mem_cache(method, key=key, maxsize=maxsize, is_global=is_global, global_name=global_name)
	if is_global:
		if global_name is None: global_name = method.__name__
		cache, cache_usage = _mem_cache_global.get(global_name, ({}, []))
	else:
		cache, cache_usage = {}, []

	def _mem_cache(method, key, maxsize):
		from functools import wraps
		if maxsize is None:
			@wraps(method)
			def _mem_cache_wrapper(*args, **kwargs):
				k = key(*args, **kwargs)
				if k in cache: return cache[k]
				res = method(*args, **kwargs)
				cache[k] = res
				return res
		else:
			@wraps(method)
			def _mem_cache_wrapper(*args, **kwargs):
				k = key(*args, **kwargs)
				if k in cache:
					res = cache[k]
					cache_usage.remove(k)
				else:
					res = method(*args, **kwargs)
					cache[k] = res
					if len(cache) > maxsize:
						elem = cache_usage.pop(-1)
						del cache[elem]
				cache_usage.insert(0, k)
				return res
		return _mem_cache_wrapper
	return _mem_cache(method, key, maxsize)

def clear_global_mem_cache(global_name: str = None):
	''' Clears the global memory cache. '''
	if global_name is None:
		_mem_cache_global.clear()
	else:
		_mem_cache_global.pop(global_name, None)

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

_tvshow_rename_regex = None
def tvshow_rename(path: str) -> None:
	''' Rename every TV show of a folder.
	I.e. Inception_Season_4_Episode_02_DivX-Total.mkv would be 04x02.mkv. '''
	from os import listdir, rename
	global _tvshow_rename_regex
	if _tvshow_rename_regex is None:
		from regex import compile
		_tvshow_rename_regex = compile(r'(?P<SEASON>\d+)\s*[x\-]\s*(?P<EPISODE>\d+)|S\s*(?P<SEASON>\d+)\s*E\s*(?P<EPISODE>\d+)|(?P<EPISODE>\d+)').search
	for file in listdir(path):
		name, ext = file.rsplit('.', 1)
		match = _tvshow_rename_regex(name.replace('_', ' '))
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
		from os import listdir
		from os.path import isdir, islink, join
		res = {}
		for child in listdir(path):
			if not any(child.endswith(ext) for ext in ignored):
				full = join(path, child)
				is_dir = 'dir' if isdir(full) else 'file'
				if not islink(full):  # symbolic links are ignored in the comparison
					res[(is_dir, child)] = full
		return res
	if kind == 'file':
		from filecmp import cmp
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

def import_from_path(path: str, name: str, module_name: str = '.') -> object:
	''' Loads the script at the specified path and returns an object given its name. '''
	from importlib.util import spec_from_file_location, module_from_spec
	from os.path import exists
	if exists(path):
		spec = spec_from_file_location(module_name, path)
		module = module_from_spec(spec)
		spec.loader.exec_module(module)
		if name in module.__dict__:
			return module.__dict__[name]