from datetime import timedelta, datetime
from difflib import SequenceMatcher
from functools import reduce
from itertools import zip_longest, compress, chain, product, combinations
from math import sqrt, ceil
from typing import Generator

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

def base_change(n: list, base_from: int, base_to: int) -> list:
	''' Changes the base of n represented as a list of integers.
	Example:  base_change([1, 1, 0, 1], 2, 10) = [1, 3]
	'''
	res = []
	n = sum(base_from ** (len(n) - i - 1) * v for i, v in enumerate(n))
	while n:
		n, digit = divmod(n, base_to)
		res.insert(0, digit)
	return res

def prime_list(n: int) -> list:
	''' Returns the list of prime numbers from 2 to n. '''
	sieve = [True] * int(n / 2)
	for i in range(3, ceil(sqrt(n)), 2):
		if sieve[int(i / 2)]:
			sieve[int(i * i / 2)::i] = [False] * int((n - i * i - 1) / (2 * i) + 1)
	return [2] + [2 * i + 1 for i in range(1, int(n / 2)) if sieve[i]]

def is_prime(n: int) -> bool:
	''' Checks if a number is prime. '''
	res = True
	if n == 2 or n == 3:
		res = True
	elif n < 2 or n % 2 == 0:
		res = False
	elif n < 9:
		res = True
	elif n % 3 == 0:
		res = False
	r = int(sqrt(n))
	f = 5
	while f <= r:
		if n % f == 0 or n % (f + 2) == 0:
			res = False
		else:
			f += 6
	return res

def fibonacci(n: int) -> int:
	''' Returns the n-th Fibonacci number. '''
	def _fib(n):
		if n == 0:
			return (0, 1)
		else:
			a, b = _fib(n // 2)
			c = a * (2 * b - a)
			d = b * b + a * a
			if n % 2 == 0:
				return (c, d)
			else:
				return (d, c + d)
	return _fib(n)[0]

def lcm(a: int, b: int) -> int:
	''' Least common multiple of two numbers. '''
	return a * b / gcd(a, b)

def gcd(a: int, b: int) -> int:
	''' Greatest common divisor of two numbers. '''
	if a < 0:
		a = -a
	if b < 0:
		b = -b
	if a == 0:
		return b
	while (b):
		a, b = b, a % b
	return a

def factor(n: int) -> list:
	''' Returns the factors of n and its exponents. '''
	f, factors, prime_gaps = 1, [], [2, 4, 2, 4, 6, 2, 6, 4]
	if n < 1:
		return []
	while True:
		for gap in ([1, 1, 2, 2, 4] if f < 11 else prime_gaps):
			f += gap
			if f * f > n:  # If f > sqrt(n)
				if n == 1:
					return factors
				else:
					return factors + [(n, 1)]
			if not n % f:
				e = 1
				n //= f
				while not n % f:
					n //= f
					e += 1
				factors.append((f, e))

def palindrome_list(k: int) -> list:
	''' Returns a list of every palindromic number with k digits. '''
	if k == 1:
		return [1, 2, 3, 4, 5, 6, 7, 8, 9]
	return [
		sum([
			n * (10**i)
			for i, n in enumerate(
				([x] + list(ys) + [z] + list(ys)[::-1] + [x])
				if k % 2 else ([x] + list(ys) + list(ys)[::-1] + [x])
			)
		])
		for x in range(1, 10)
		for ys in product(range(10), repeat=k // 2 - 1)
		for z in (range(10) if k % 2 else (None,))
	]

def phi(n: int) -> int:
	''' Returns the Euler's phi function of n. '''
	res = n
	factors = [f[0] for f in factor(n)]
	multiplier = 1
	for fs in range(1, len(factors) + 1):
		multiplier *= -1
		for primes in combinations(factors, fs):
			val = reduce(lambda x, y: x * y, primes)
			if val <= n and n % val == 0:
				res += (n // val) * multiplier
	return res

def date_range(date_start: datetime, date_end: datetime, step: timedelta = timedelta(days=1)) -> Generator[datetime, None, None]:
	current = date_start
	while current < date_end:
		yield current
		current += step