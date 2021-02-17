from time import time
from sys import getsizeof
from types import ModuleType, FunctionType
from gc import get_referents

_tictoc_stack = []
def tic():
	''' Captures time '''
	global _tictoc_stack
	_tictoc_stack.append(time())

def toc(show=True):
	''' Shows time since tic() was executed. '''
	global _tictoc_stack
	total = time() - _tictoc_stack.pop()
	if show:
		print(total)
	else:
		return total

_deep_size_blacklist = type, ModuleType, FunctionType
def deep_size(obj):
	''' Get the actual size of an instance, exploring all its references. '''
	if isinstance(obj, _deep_size_blacklist):
		raise TypeError('getsize() does not take argument of type: ' + str(type(obj)))
	seen_ids = set()
	size = 0
	objects = [obj]
	while objects:
		need_referents = []
		for obj in objects:
			if not isinstance(obj, _deep_size_blacklist) and id(obj) not in seen_ids:
				seen_ids.add(id(obj))
				size += getsizeof(obj)
				need_referents.append(obj)
		objects = get_referents(*need_referents)
	return size