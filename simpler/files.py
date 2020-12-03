from filecmp import cmp
from json import load as jload, dump as jdump
from os import listdir, makedirs, chdir
from os.path import isdir, islink, join, exists, dirname
from pickle import load as pload, dump as pdump
from regex import compile
from time import time

REGEX_SAFE_FILENAME = compile(r'[/\\\*;\[\]\":=,<>]')
REGEX_FIND_EPISODE = compile(r'(?P<SEASON>\d+)\s*[x\-]\s*(?P<EPISODE>\d+)|S\s*(?P<SEASON>\d+)\s*E\s*(?P<EPISODE>\d+)|(?P<EPISODE>\d+)').search

def cd(directory=__file__):
	''' Change the current working directory for relative routes. '''
	chdir(dirname(directory))

_read_accepted_formats = 'string', 'bytes', 'json', 'pickle'
def read(path: str, encoding: str = 'utf-8', format: str = 'string') -> object:
	assert format in _read_accepted_formats
	if format == 'string':
		fp = open(path, 'r', encoding=encoding)
	else:
		fp = open(path, 'rb')
	if format in ('bytes', 'string'):
		res = fp.read()
	elif format == 'json':
		res = jload(fp)
	elif format == 'pickle':
		res = pload(fp)
	fp.close()
	return res

_stream_accepted_formats = 'string', 'bytes'
def stream_lines(path: str, encoding: str = 'utf-8', format: str = 'string') -> object:
	assert format in _stream_accepted_formats
	if format == 'string':
		fp = open(path, 'r', encoding=encoding)
	else:
		fp = open(path, 'rb')
	for line in fp:
		yield line
	fp.close()

_read_accepted_formats = 'string', 'bytes', 'json', 'pickle'
def read(path: str, content: object, encoding: str = 'utf-8', format: str = 'string', append: bool = False, json_ensure_ascii=False, json_indent='\t', json_separators=(', ', ': '), pickle_protocol=4) -> None:
	assert format in _read_accepted_formats
	if format == 'string':
		fp = open(path, 'a', encoding=encoding)
	else:
		fp = open(path, 'ab')
	if format in ('bytes', 'string'):
		fp.write(content)
	elif format == 'json':
		jdump(content, fp, ensure_ascii=json_ensure_ascii, indent=json_indent, separators=json_separators)
	elif format == 'pickle':
		pdump(content, fp, protocol=pickle_protocol)
	fp.close()
	return res

def cache(target, args=None, kwargs=None, name=None, cache_lifespan=None, cache_directory='.pickled/'):
	''' Runs the `target` method with the given `args` and `kwargs`, and store
	its result to a pickled cache folder using the name of the target method,
	or an alternative `name`, if given. If `cache_lifespan` is set, the stored
	result will be discarded after `cache_lifespan` seconds. '''
	args = () if args is None else args
	kwargs = {} if kwargs is None else kwargs
	name = REGEX_SAFE_FILENAME.sub(target.__name__ if name is None else name)
	makedirs(cache_directory, exist_ok=True)
	path = join(cache_directory, '_', name) + '.pk'
	now = time()
	res = None
	if exists(path):
		with open(path, 'rb') as fp:
			save_time, value = pload(fp)
		if cache_lifespan is None or now < save_time + cache_lifespan:
			res = value
	if res is None:
		res = target(*args, **kwargs)
		with open(path, 'wb') as fp:
			pdump((now, res), fp, protocol=3)
	return res

def size(file):
	''' A way to see the size of a file without loading it to memory.
	See https://stackoverflow.com/a/22126842/1832728 '''
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

_directory_compare_ignored = ('.class', '.metadata', '.recommenders', '.pyc', '.git', '.svn', '.cache', '__pycache__')
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
				compare(old_childs[child], new_childs[child], child[0])