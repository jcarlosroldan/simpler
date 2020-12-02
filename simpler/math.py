from difflib import SequenceMatcher

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

def clamp(value, smallest=0, largest=1):
	return max(smallest, min(value, largest))

def unique(lst: list, uniqueness_function):
	''' Returns a list in the same order with just the elements with a unique
	value on the uniqueness_function.
	I.e.: `unique([1, 5, 7, 9], lambda x: x % 3)` would return [1, 5, 9].'''
	values = []
	keys = []
	for v in lst:
		k = uniqueness_function(v)
		if k not in keys:
			keys.append(k)
			values.append(v)
	return values

def all_equal(lst):
	return len(lst) < 2 or all(lst[0] == e for e in lst[1:])

def jaccard(seq1, seq2):
	set1, set2 = set(seq1), set(seq2)
	return len(set1.intersection(set2)) / len(set1.union(set2))

def levenshein(seq1, seq2):
    return SequenceMatcher(None, a, b).ratio()