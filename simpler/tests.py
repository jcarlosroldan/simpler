from typing import Dict, List, Optional, Tuple

class Test:
	''' Class for a test case. Each test case might contain multiple `test_<something>` methods
	which are called when running the tests. It is advisable to run it from the `simpler.Suite` class. '''
	PREFIX = 'test_'

	def run(self) -> Dict[str, Tuple[Optional[str], float]]:
		''' Internal method used to run the tests. '''
		from time import time
		from traceback import format_exc
		res = {}
		total_elapsed = passes = errors = 0
		for name in self.__dir__():
			if not name.startswith(self.PREFIX): continue
			method = self.__getattribute__(name)
			elapsed = time()
			try:
				method()
				output = None
			except AssertionError as e:
				output = e.args[0]
			except:
				output = 'Error while running the test:\n' + format_exc()
			elapsed = time() - elapsed
			total_elapsed += elapsed
			res[name[len(self.PREFIX):]] = output, elapsed
			if output is None:
				passes += 1
			else:
				errors += 1
		return res, total_elapsed, passes, errors

class Suite:
	''' Class for running a test suite. Is built as Suite(FirstTest, SecondTest...) where the
	arguments are an enumeration of subclasses of `simpler.Test` classes that will be run when using
	this class `run` method. There are a few `run_<format>` methods to get a formatted output. '''

	def __init__(self, *tests: List[Test]) -> None:
		assert all(t.__name__.endswith('Test') for t in tests), 'All test classes must end with "Test".'
		self.tests = tests

	def run(self) -> Tuple[Dict[str, Tuple[Dict[str, Tuple[Optional[str], float]], float, int, int]], float, int, int]:
		''' Runs the tests and returns a dictionary of tests, where each test is a dictionary of
		`case: error` pairs. '''
		res = {}
		total_elapsed = total_errors = total_passes = 0
		for test in self.tests:
			output, elapsed, passes, errors = test().run()
			total_elapsed += elapsed
			total_errors += errors
			total_passes += passes
			if len(output):
				res[test.__name__[:-4]] = output, elapsed, errors, passes
		return res, total_elapsed, total_passes, total_errors

	def run_text(self, only_errors: bool = True) -> Optional[str]:
		''' Runs the `run` method and formats the output as a plain text. '''
		tests, elapsed, passes, errors = self.run()
		if errors or not only_errors:
			res = 'Summary: %d errors and %d passes in %.2fs.\n' % (errors, passes, elapsed)
			for test, (cases, test_elapsed, test_passes, test_errors) in tests.items():
				if only_errors and test_errors == 0: continue
				res += 'Test %s (%d/%d in %.2fs)\n' % (test, test_errors, test_errors + test_passes, test_elapsed)
				for case, (message, elapsed) in cases.items():
					if only_errors and message is None: continue
					res += '\tCase %s (%.2fs)' % (case, elapsed)
					res += ': PASS\n' if message is None else ': ERROR\n%s\n' % '\n'.join('\t\t%s' % line for line in message.strip().split('\n'))
			return res.strip()

	def run_html(self, only_errors: bool = True) -> Optional[str]:
		''' Runs the `run` method and returns a table of errors, or None if there isn't any. '''
		tests, elapsed, passes, errors = self.run()
		if errors or not only_errors:
			res = '<p><b>Summary: %d errors and %d passes in %.2fs.</b></p><table><tr><th>Test</th><th>Case</th><th>Elapsed (s)</th><th>%s</th></tr>' % (
				errors, passes, elapsed, 'Error' if only_errors else 'Result'
			)
			for test, (cases, _, _, _) in tests.items():
				for case, (message, elapsed) in cases.items():
					if message is not None or not only_errors:
						res += '<tr><td>%s</td><td>%s</td><td>%.2f</td><td><div style="font-family:monospace;white-space:pre;max-width:35rem;overflow:auto">%s</div></td></tr>' % (test, case, elapsed, ('<span style="color:#080">✓</span>' if message is None else message))
			if not only_errors:
				res += '<tr><th colspan=2>Total</th><td>%.2f</td><td>%d/%d OK</td></tr>' % (elapsed, passes, passes + errors)
			return res + '</table>'