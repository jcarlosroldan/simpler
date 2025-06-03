from typing import Optional, Type

class Test:
	''' Class for a test case. Each test case might contain multiple `test_<something>` methods
	which are called when running the tests. It is advisable to run it from the `simpler.Suite` class. '''
	PREFIX = 'test_'

	def run(self, only_errors: bool = True) -> dict:
		''' Internal method used to run the tests. '''
		from time import time
		from traceback import format_exc
		res = {'oks': 0, 'errors': 0, 'elapsed': 0, 'cases': {}}
		for name in dir(self):
			if not name.startswith(self.PREFIX): continue
			case = getattr(self, name)
			elapsed = time()
			error = None
			try:
				case()
				res['oks'] += 1
			except AssertionError as e:
				error = e.args[0] if e.args else ''
				res['errors'] += 1
			except:
				error = 'There was an uncaught error while running the test.\n' + format_exc()
				res['errors'] += 1
			elapsed = time() - elapsed
			res['elapsed'] += elapsed
			if not only_errors or error is not None:
				res['cases'][name[len(self.PREFIX):]] = {'elapsed': elapsed, 'error': error}
		return res

class Suite:
	''' Class for running a test suite. Is built as Suite(FirstTest, SecondTest...) where the
	arguments are an enumeration of subclasses of `simpler.Test` classes that will be run when using
	this class `run` method. There are a few `run_<format>` methods to get a formatted output. '''

	def __init__(self, *tests: Type[Test]) -> None:
		assert all(t.__name__.endswith('Test') for t in tests), 'All test classes must end with "Test".'
		self.tests = tests

	def run(self, only_errors: bool = True) -> dict:
		''' Runs the tests and returns a dictionary of tests, where each test is a dictionary of
		`case: error` pairs. '''
		res = {'_total': {'oks': 0, 'errors': 0, 'elapsed': 0}}
		for test in self.tests:
			name = test.__name__[:-4]
			test = test().run(only_errors)
			res['_total']['elapsed'] += test['elapsed']
			res['_total']['oks'] += test['oks']
			res['_total']['errors'] += test['errors']
			if not only_errors or test['errors']:
				res[name] = test
		return res

	def run_text(self, only_errors: bool = True) -> Optional[str]:
		''' Runs the `run` method and formats the output as a plain text. '''
		res = self.run(only_errors)
		if only_errors and res['_total']['errors'] == 0: return None
		output = f'Summary: {res["_total"]["errors"]} errors and {res["_total"]["oks"]} passes in {res["_total"]["elapsed"]:.2f}s.\n'
		for name, data in res.items():
			if name == '_total': continue
			output += f'Test {name} ({data["errors"]}/{data["oks"] + data["errors"]} in {data["elapsed"]:.2f}s)\n'
			for case, details in data['cases'].items():
				output += f'\tCase {case} ({details["elapsed"]:.2f}s)'
				if details['error'] is None:
					output += ': PASS\n'
				else:
					output += ': ERROR\n\t\t%s\n' % details['error'].replace('\n', '\n\t\t')
		return output.strip()

	def run_html(self, only_errors: bool = True) -> Optional[str]:
		''' Runs the `run` method and returns a table of errors, or None if there isn't any. '''
		res = self.run(only_errors)
		if only_errors and res['_total']['errors'] == 0: return None
		output = f'<p><b>Summary:</b> {res["_total"]["errors"]} errors and {res["_total"]["oks"]} passes in {res["_total"]["elapsed"]:.2f}s.</p><table><tr><th>Test</th><th>Case</th><th>Elapsed (s)</th><th>Error</th></tr>'
		for name, data in res.items():
			if name == '_total': continue
			for case, details in data['cases'].items():
				output += f'<tr><td>{name}</td><td>{case}</td><td>{details["elapsed"]:.2f}</td>'
				if details['error'] is None:
					output += '<td><span style="color:#080">✓</span></td></tr>'
				else:
					output += '<td><div style="font-family:monospace;white-space:pre;max-width:35rem;overflow:auto">%s</div></td></tr>' % details['error'].replace('\n', '<br>')
		if not only_errors:
			output += f'<tr><th colspan=2>Total</th><td>{res["_total"]["elapsed"]:.2f}</td><td>{res["_total"]["oks"]}/{res["_total"]["errors"] + res["_total"]["oks"]} OK</td></tr>'
		return output + '</table>'

	def run_markdown(self, only_errors: bool = True) -> Optional[str]:
		res = self.run(only_errors)
		if only_errors and res['_total']['errors'] == 0: return None
		output = f'**Summary:** {res["_total"]["errors"]} errors and {res["_total"]["oks"]} passes in {res["_total"]["elapsed"]:.2f}s.\n\n'
		for name, data in res.items():
			if name == '_total': continue
			output += f'* **{name}** ({data["errors"]}/{data["oks"] + data["errors"]} in {data["elapsed"]:.2f}s)\n'
			for case, details in data['cases'].items():
				if details['error'] is None:
					output += f'  * {case} ({details["elapsed"]:.2f}s): ✓ PASS\n'
				else:
					output += '  * %s (%.2fs): ❌ ERROR\n    ```\n    %s\n    ```\n' % (case, details['elapsed'], details['error'].replace('\n', '\n    '))
		return output.strip()