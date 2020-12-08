from difflib import SequenceMatcher

def clamp(value: float, smallest: float = 0, largest: float = 1) -> float:
	''' Returns the value clamped between smallest and largest.
	I.e.: `clamp(10, 2, 8)` would return 8. '''
	return max(smallest, min(value, largest))

def snap(value: float, step: float = 1, offset: float = 0) -> float:
	''' Returns the value snapped to a scale of size step with an optional offset.
	I.e.: `snap(3.1, 2, 0)` would return 4. '''
	return round((value - offset) / step) * step + offset

def unique(seq: list, uniqueness_function) -> list:
	''' Returns a list in the same order with just the elements with a unique
	value on the uniqueness_function.
	I.e.: `unique([1, 5, 7, 9], lambda x: x % 3)` would return [1, 5, 9]. '''
	values = []
	keys = []
	for elem in seq:
		k = uniqueness_function(elem)
		if k not in keys:
			keys.append(k)
			values.append(elem)
	return values

def all_equal(seq: list) -> list:
	''' Returns true if every element in the sequence has the same value. '''
	return len(seq) < 2 or all(seq[0] == e for e in seq[1:])

def jaccard(seq1: list, seq2: list) -> list:
	''' Returns the Jaccard index of two sequences. '''
	set1, set2 = set(seq1), set(seq2)
	return len(set1.intersection(set2)) / len(set1.union(set2))

def levenshtein(seq1: list, seq2: list) -> list:
	''' Returns the Levenshtein distance of two sequences. '''
	return SequenceMatcher(None, seq1, seq2).ratio()

def base_change(number: list, base_from: int, base_to: int) -> list:
	''' Changes the base of a number represented as a list of integers.
	Example:  base_change([1, 1, 0, 1], 2, 10) = [1, 3]
	'''
	res = []
	n = sum(base_from ** (len(number) - i - 1) * v for i, v in enumerate(number))
	while n:
		n, digit = divmod(n, base_to)
		res.insert(0, digit)
	return res