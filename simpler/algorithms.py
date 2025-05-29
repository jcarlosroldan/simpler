class DynamicProgramming:
	ONE_SOLUTION = 0
	ONE_OPTIMAL_SOLUTION = 1
	ALL_SOLUTIONS = 2
	ALL_OPTIMAL_SOLUTIONS = 3

	def __init__(self, initial_state):
		self.initial_state = initial_state

	def alternatives(self, state: object) -> list:
		''' This should return all the alternatives for a given state, without modifying the given state. '''
		raise NotImplementedError()

	def is_final(self, state: object) -> bool:
		''' This should return whether a state is a final state or not. '''
		raise NotImplementedError()

	def penalty(self, state: object) -> float:
		''' This should return an upper bound for the penalty of the problem. Ideally, optimal solutions should have no penalty. '''
		raise NotImplementedError()

	def solve(self, search_type: int = ONE_SOLUTION):
		assert search_type in range(4), 'Invalid search type.'
		final_states = []
		explored = set()
		remaining = [(self.penalty(self.initial_state), self.initial_state)]
		while len(remaining):
			_, state = remaining.pop(0)
			explored.add(state)
			for alternative in self.alternatives(state):
				if alternative in explored: continue
				penalty = self.penalty(alternative)
				if self.is_final(alternative):
					if search_type == self.ONE_SOLUTION or penalty == 0 and search_type == self.ONE_OPTIMAL_SOLUTION:
						return alternative
					else:
						final_states.append((penalty, alternative))
				else:
					index = sum(1 for p, _ in remaining if p < penalty)
					remaining.insert(index, (penalty, alternative))
		if not final_states: return None
		if search_type == self.ALL_SOLUTIONS:
			return [state for _, state in final_states]
		else:
			min_penalty = min([penalty for penalty, _ in final_states])
			optimals = [state for penalty, state in final_states if penalty == min_penalty]
			if search_type == self.ALL_OPTIMAL_SOLUTIONS:
				return optimals
			else:
				return optimals[0]

def deep_merge(dict1: dict, dict2: dict) -> dict:
	''' This function merges two dictionaries. '''
	from copy import deepcopy
	res = deepcopy(dict1)
	for key, value in dict2.items():
		if key in res and isinstance(res[key], dict) and isinstance(value, dict):
			res[key] = deep_merge(res[key], value)
		else:
			res[key] = deepcopy(value)
	return res