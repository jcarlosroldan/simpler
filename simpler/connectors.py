from typing import Union, Any, Generator, List, Optional
from MySQLdb import Connection
from pandas import ExcelFile, read_excel, DataFrame, concat
from numpy import arange, concatenate, array
from re import compile, IGNORECASE

class MySQL:
	''' Connector for the MySQLdb backend with a handful of helpers. '''
	def __init__(
		self, host: str, user: str, password: str = None, db: str = None, charset: str = 'utf8mb4',
		use_unicode: bool = True, autocommit: bool = True, max_insertions: int = None
	) -> None:
		self.max_insertions, self._cursor = max_insertions, None
		self._connection = {
			'host': host,
			'user': user,
			'charset': charset,
			'use_unicode': use_unicode,
			'autocommit': autocommit
		}
		if password:
			self._connection.update({'passwd': password, 'auth_plugin': 'mysql_native_password'})
		if db:
			self._connection['db'] = db
	
	def __del__(self):
		self.close()

	def close(self) -> None:
		''' Closes the current cursor and connection. '''
		if self._cursor is not None:
			self._cursor.close()
			self._connection.close()

	def get_cursor(self):
		''' Returns the open cursor and initializes the connection if required. '''
		if self._cursor is None:
			self._connection = Connection(**self._connection)
			self._cursor = self._connection.cursor()
		return self._cursor
	
	def execute(self, query: str, params: tuple = None):
		''' Wrapper for the MySQLdb execute method that won't send the params argument
		if the params are empty, thus avoiding the need to replace % with %%. '''
		return self.get_cursor().execute(query, params if len(params) else None)

	def find(self, query: str, *params: tuple) -> dict:
		''' Returns a {column: value} dict of the first selected row. '''
		row = self.find_one_tuple(query, *params)
		if row:
			return {k[0]: v for k, v in zip(self.get_cursor().description, row)}
	
	def find_tuple(self, query: str, *params: tuple) -> tuple:
		''' Returns a tuple of the values of the first selected row. '''
		self.execute(query, params)
		return self.get_cursor().fetchone()

	def find_all(self, query: str, *params: tuple) -> List[dict]:
		''' Returns a list of {column: value} dicts of the selected rows. '''
		return list(self.iter_all(query, *params))

	def find_all_tuples(self, query: str, *params: tuple) -> List[tuple]:
		''' Returns a list of tuples of the selected rows. '''
		return list(self.iter_all_tuples(query, *params))

	def iter_all(self, query: str, *params: tuple) -> Generator[dict, None, None]:
		''' Returns a generator of {column: value} dicts of the selected rows. '''
		rows = self.iter_many_tuples(query, *params)
		description = self.get_cursor().description
		for row in rows:
			yield {k[0]: v for k, v in zip(description, row)}

	def iter_all_tuples(self, query: str, *params: tuple) -> Generator[tuple, None, None]:
		''' Returns a generator of tuples of the selected rows. '''
		self.execute(query, params)
		return self.get_cursor().fetchall()

	def find_value(self, query: str, *params: tuple) -> Any:
		''' Returns the value of the first column of the first selected row. '''
		self.execute(query, params)
		res = self.get_cursor().fetchone()
		if res:
			return res[0]

	def find_column(self, query: str, *params: tuple) -> list:
		''' Returns the value of the first column of every selected row. '''
		return list(self.iter_column(query, *params))

	def iter_column(self, query: str, *params: tuple) -> Generator[list, None, None]:
		''' Returns a generator of the first column of every selected row. '''
		self.execute(query, params)
		for row in self.get_cursor().fetchall():
			yield row[0]

	def insert(self, query: str, *params: tuple) -> int:
		''' Inserts a row and returns its id. '''
		self.execute(query, params)
		return int(self.get_cursor().lastrowid)

	def insert_all(self, table: str, rows: list, tuple_rows: bool = True) -> Optional[int]:
		''' Insert a list of rows and returns the id of the last one. By default,
		these rows are a list of {column: value} dicts, but they can be inserted
		from tuples of values setting `tuple_rows` to True. '''
		if not len(rows): return
		while self.max_insertions is not None and self.max_insertions < len(rows):
			part, rows = rows[:self.max_insertions], rows[self.max_insertions:]
			self.insert_many(table, part, tuple_rows)
		if tuple_rows:
			query = 'INSERT INTO %s VALUES %s' % (
				table,
				','.join(['(' + ','.join(['%s'] * len(rows[0])) + ')'] * len(rows))
			)
			params = [param for row in rows for param in row]
		else:
			keys = list(rows[0].keys())
			values = '(%s)' % ','.join('%s' for _ in keys)
			query = 'INSERT INTO %s(%s) VALUES %s' % (
				table,
				','.join(keys),
				','.join(values for _ in rows)
			)
			params = [insertion[key] for insertion in rows for key in keys]
		self.execute(query, params)
		return int(self.get_cursor().lastrowid)

	def apply(self, query: str, *params: tuple) -> int:
		''' Applies a modification (update or delete) and returns the number of affected rows. '''
		self.execute(query, params)
		return int(self.get_cursor().rowcount)

	def update(self, table: str, updates: dict = lambda: {}, filters: dict = lambda: {}) -> int:
		''' Executes an update operation and returns the number of affected rows, specifying
		a {column: value} list of updates and a filters list, i.e. `{'a': 4, 'b': None}` will be
		translated into `WHERE A = 4 and B = NULL`. '''
		query = 'UPDATE %s ' % table
		params = []
		if len(updates):
			values = []
			for k, v in updates.items():
				values.append(k + '=%s')
				params.append(v)
			query += 'SET ' + ','.join(values)
		if len(filters):
			values = []
			for k, v in filters.items():
				values.append(k + '=%s')
				params.append(v)
			query += 'WHERE ' + ' AND '.join(values)
		self.execute(query, params)
		return int(self.get_cursor().rowcount)

	def escape(self, value: Any, is_literal: bool = True) -> str:
		''' Escapes the given value for its injection into the SQL query. By default,
		the data `is_literal=True`, which will wrap strings with quotes for its insertion. '''	
		if value is None:
			value = 'NULL'
		elif type(value) == str:
			value = self._connection.escape_string(value).decode()
			if is_literal:
				value = '"%s"' % value
		else:
			value = self._connection.string_literal(value).decode()
		return value

class Excel:
	''' Pandas Excel backend. '''

	_RANGE = compile(r'(?P<start_col>[a-z]+)(?P<start_row>\d+)(\:(?P<end_col>[a-z]+)(?P<end_row>\d+))?', flags=IGNORECASE).match
	_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

	def __init__(self, path: str):
		self.path = path
		self.sheet_names = ExcelFile(path).sheet_names
		self.sheets = {name: None for name in self.sheet_names}

	def sheet(self, sheet: Union[str, int] = 0) -> DataFrame:
		''' Loads a sheet given its name or position in the book. '''
		if isinstance(sheet, int):
			sheet = self.sheet_names[sheet]
		if self.sheets[sheet] is None:
			self.sheets[sheet] = read_excel(
				self.path,
				dtype=str,
				sheet_name=sheet,
				na_filter=False,
				header=None
			).applymap(lambda x: x.strip() if isinstance(x, str) else x)
		return self.sheets[sheet]

	def cell(self, row: int, col: int, sheet: int = 0) -> DataFrame:
		''' Retrieves a cell from the book. '''
		return self.sheet(sheet).iloc[row].iloc[col]

	def cells(self, block: Union[str, int], sheet: int = 0) -> DataFrame:
		''' Retrieves a square of cells data from a block. '''
		if isinstance(block, str):
			block = self.block_from_code(block)
		return self.sheet(sheet).iloc[block[0]:block[2], block[1]:block[3]]

	def index_from_code(self, code: str) -> int:
		''' Transforms an Excel code like ABC to an index like 731.'''
		res = 0
		for letter in code:
			res = res * len(Excel._LETTERS) + Excel._LETTERS.index(letter) + 1
		return res

	def block_from_code(self, code: str) -> tuple:
		''' Transforms an Excel code like A4:B5 to block delimiters like (3, 0, 5, 2). '''
		match = Excel._RANGE(code)
		assert match, 'Excel range %s is not valid' % code
		return (
			int(match.group('start_row')) - 1,
			self.index_from_code(match.group('start_col')) - 1,
			int(match.group('end_row')),
			self.index_from_code(match.group('end_col'))
		)

	def table(
		self, data: Union[tuple, str], hrows: Union[tuple, str] = None,
		hcols: Union[tuple, str] = None, sheet: Union[int, str] = 0
	) -> array:
		data = self.cells(data, sheet=sheet)
		rows, cols = data.shape
		data = data.stack().values.reshape(-1, 1)
		if hrows:
			if isinstance(hrows, str):
				hrows = (hrows,)
			for hrow in hrows:
				header = self.cells(hrow, sheet=sheet)
				header = concat([header] * rows, axis=1).transpose().values
				data = concatenate([data, header], axis=1)
		if hcols:
			if isinstance(hcols, str):
				hcols = (hcols,)
			for hcol in hcols:
				header = self.cells(hcol, sheet=sheet)
				header = header.iloc[arange(len(header)).repeat(cols)].values
				data = concatenate([data, header], axis=1)
		return data

	def __str__(self) -> str:
		return 'Excel(path="%s")' % self.path