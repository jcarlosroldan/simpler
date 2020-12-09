from time import time

# Tic-toc function
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