from numpy import arange, array, concatenate
from pandas import concat, DataFrame, ExcelFile, read_excel
from re import compile, IGNORECASE
from simpler.terminal import cprint
from typing import Any, Generator, List, Optional, Union

def _mysql_converter():
	''' Simpler MySQL converter that returns some bytes as strings and decimals as floats. '''
	from mysql.connector.constants import FieldFlag
	from mysql.connector.conversion import MySQLConverter as NativeConverter

	class MySQLConverter(NativeConverter):
		def row_to_python(self, row, fields):
			res = super().row_to_python(row, fields)
			return res

		def _BLOB_to_python(self, value, dsc=None):
			"""Convert BLOB data type to Python"""
			return self._STRING_to_python(value, dsc)
		_LONG_BLOB_to_python = _BLOB_to_python
		_MEDIUM_BLOB_to_python = _BLOB_to_python
		_TINY_BLOB_to_python = _BLOB_to_python

		def _DECIMAL_to_python(self, value, desc=None):
			return float(value.decode(self.charset))
		_NEWDECIMAL_to_python = _DECIMAL_to_python

		def _float64_to_mysql(self, value, desc=None):
			return float(value)

		def _STRING_to_python(self, value, dsc=None):
			res = super(MySQLConverter, self)._STRING_to_python(value, dsc)
			if dsc[7] & FieldFlag.BINARY:
				return res.decode(self.charset)
			return res
		_VAR_STRING_to_python = _STRING_to_python

	return MySQLConverter

class SQL:
	''' Connector for SQL databases with a handful of helpers. '''
	ENGINES = 'mysql', 'mariadb', 'mssql'
	def __init__(
		self, host: str = 'localhost', user: str = 'root', password: str = None, db: str = None,
		charset: str = 'utf8mb4', collation: str = 'utf8mb4_general_ci', use_unicode: bool = True,
		max_insertions: int = None, print_queries: bool = False, native_types: bool = True,
		engine: str = 'mysql'
	) -> None:
		assert engine in SQL.ENGINES, 'Accepted engine values are: %s.' % ', '.join(SQL.ENGINES)
		self.max_insertions, self.native_types, self.engine, self.print_queries = max_insertions, native_types, engine, print_queries
		self._connection, self._cursor, self._initialized = {'user': user}, {}, False
		if engine in ('mysql', 'mariadb'):
			self._init_mysql(charset, collation, host, use_unicode, password, db)
		elif engine == 'mssql':
			self._init_mssql(host, password, db)
	
	def _init_mysql(self, charset, collation, host, use_unicode, password, db):
		self._connection.update({
			'charset': charset,
			'collation': collation,
			'host': host,
			'use_unicode': use_unicode
		})
		if password:
			self._connection.update({
				'passwd': password,
				'auth_plugin': 'mysql_native_password'
			})
		if db:
			self._connection['db'] = db
		self._cursor['buffered'] = True
	
	def _init_mssql(self, host, password, db):
		self._connection['server'] = host
		if password:
			self._connection['password'] = password
		if db:
			self._connection['database'] = db

	def close(self) -> None:
		''' Closes the current cursor and connection. '''
		if self._initialized:
			self._cursor.close()
			self._connection.close()
			self._initialized = False

	__del__ = close

	def cursor(self):
		''' Returns the open cursor and initializes the connection if required. '''
		if not self._initialized:
			if self.engine in ('mysql', 'mariadb'):
				try:
					from mysql.connector import connect
				except ModuleNotFoundError:
					raise ModuleNotFoundError('Missing MySQL/MariaDB connector. Install a mysql client and then do `pip install mysql.connector`.')
				if self.native_types:
					self._connection['converter_class'] = _mysql_converter()
			else:
				try:
					from pymssql import connect
				except ModuleNotFoundError:
					raise ModuleNotFoundError('Missing MS-SQL connector. Install a MS-SQL client and then do `pip install pymssql`.')
			self._connection = connect(**self._connection)
			self._cursor = self._connection.cursor(**self._cursor)
			self._initialized = True
		return self._cursor

	def execute(self, query: str, params: tuple = None, multi: bool = False, commit: bool = False):
		''' Wrapper for the database connector execute method that won't send the params argument
		if the params are empty, thus avoiding the need to replace % with %%. '''
		if self.print_queries:
			self.print_query(query, params)
		error = None
		try:
			if self.engine == 'mysql':
				statement = self.cursor().execute(query, params if params is not None and len(params) else None, multi)
				if multi:
					try:
						list(statement)
					except RuntimeError:  # see https://bugs.mysql.com/bug.php?id=87818
						pass
			else:
				assert not multi, 'MS-SQL connector does not support multistatement queries.'
				statement = self.cursor().execute(*([query] + ([params] if params else [])))
		except Exception as e:
			error = e
		if self._initialized and (commit or self.engine in ('mysql', 'mariadb')):
			self._connection.commit()
		if error is not None:
			raise error

	def print_query(self, query: str, params: tuple = None, color: str = 'yellow', max_size: int = 1000):
		''' Shows a query attempting to inject the parameters, for debugging purposes. '''
		if len(query) > max_size:
			query = query[:max_size // 2] + '...' + query[-max_size // 2:]
		try:
			formatted = query.strip() % params if params is not None and len(params) else query.strip()
		except:
			formatted = query.strip()
		cprint(formatted + ';', fg=color)

	def select(
		self, table: str, filters: dict = lambda: {}, first_row: bool = False,
		first_column: bool = False, tuple_rows: bool = True, or_filters: bool = False
	) -> int:
		''' Executes an select operation and returns the resulting rows, specifying a filters
		list, i.e. `{'a': 4, 'b': None}` will be translated into `WHERE A = 4 and B = NULL`. '''
		query = 'SELECT * FROM %s ' % table
		columns = list(filters.keys())
		params = [filters[c] for c in columns]
		if len(columns):
			query += ' WHERE ' + (' OR ' if or_filters else ' AND ').join(c + '=%s' for c in columns)
		self.execute(query, params)
		res = [self.cursor().fetchone()] if first_row else list(self.cursor().fetchall())
		res = [row[0] if first_column else row for row in res]
		if not tuple_rows:
			description = self.cursor().description
			res = [{k[0]: v for k, v in zip(description, row)} for row in res]
		return res[0] if first_row else res

	def find(self, query: str, *params: tuple) -> dict:
		''' Returns a {column: value} dict of the first selected row. '''
		row = self.find_tuple(query, *params)
		if row:
			return {k[0]: v for k, v in zip(self.cursor().description, row)}

	def find_tuple(self, query: str, *params: tuple) -> tuple:
		''' Returns a tuple of the values of the first selected row. '''
		self.execute(query, params)
		return self.cursor().fetchone()

	def find_all(self, query: str, *params: tuple) -> List[dict]:
		''' Returns a list of {column: value} dicts of the selected rows. '''
		return list(self.iter_all(query, *params))

	def find_all_tuples(self, query: str, *params: tuple) -> List[tuple]:
		''' Returns a list of tuples of the selected rows. '''
		return list(self.iter_all_tuples(query, *params))

	def iter_all(self, query: str, *params: tuple) -> Generator[dict, None, None]:
		''' Returns a generator of {column: value} dicts of the selected rows. '''
		rows = self.iter_all_tuples(query, *params)
		description = self.cursor().description
		for row in rows:
			yield {k[0]: v for k, v in zip(description, row)}

	def iter_all_tuples(self, query: str, *params: tuple) -> Generator[tuple, None, None]:
		''' Returns a generator of tuples of the selected rows. '''
		self.execute(query, params)
		return self.cursor().fetchall()

	def find_value(self, query: str, *params: tuple) -> Any:
		''' Returns the value of the first column of the first selected row. '''
		self.execute(query, params)
		res = self.cursor().fetchone()
		if res:
			return res[0]

	def find_column(self, query: str, *params: tuple) -> list:
		''' Returns the value of the first column of every selected row. '''
		return list(self.iter_column(query, *params))

	def iter_column(self, query: str, *params: tuple) -> Generator[list, None, None]:
		''' Returns a generator of the first column of every selected row. '''
		self.execute(query, params)
		for row in self.cursor().fetchall():
			yield row[0]

	def insert(self, query: str, *params: tuple) -> int:
		''' Inserts a row and returns its id. '''
		self.execute(query, params, commit=True)
		return int(self.cursor().lastrowid)

	def insert_all(self, table: str, rows: Union[List[dict], List[tuple]], tuple_rows: bool = True, commit: bool = True) -> Optional[int]:
		''' Insert a list of rows and returns the id of the last one. By default,
		these rows are a list of {column: value} dicts, but they can be inserted
		from tuples of values setting `tuple_rows` to True. '''
		if not len(rows): return
		while self.max_insertions is not None and self.max_insertions < len(rows):
			part, rows = rows[:self.max_insertions], rows[self.max_insertions:]
			self.insert_all(table, part, tuple_rows, commit=False)
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
		self.execute(query, params, commit=commit)
		return int(self.cursor().lastrowid)

	def apply(self, query: str, *params: tuple) -> int:
		''' Applies a modification (update or delete) and returns the number of affected rows. '''
		self.execute(query, params, commit=True)
		return int(self.cursor().rowcount)

	def update(self, table: str, updates: dict = lambda: {}, filters: dict = lambda: {}) -> int:
		''' Executes an update operation and returns the number of affected rows, specifying
		a {column: value} list of updates and a filters list, i.e. `{'a': 4, 'b': None}` will be
		translated into `WHERE A = 4 and B = NULL`. '''
		query = 'UPDATE %s ' % table
		# TODO use max_insertions here too
		params = []
		if len(updates):
			values = []
			for k, v in updates.items():
				values.append(k + '=%s ')
				params.append(v)
			query += 'SET ' + ','.join(values)
		if len(filters):
			values = []
			for k, v in filters.items():
				values.append(k + '=%s ')
				params.append(v)
			query += 'WHERE ' + ' AND '.join(values)
		self.execute(query, params, commit=True)
		return int(self.cursor().rowcount)

	def escape(self, value: Any, is_literal: bool = True) -> str:
		''' Escapes the given value for its injection into the SQL query. By default,
		the data `is_literal=True`, which will wrap strings with quotes for its insertion. '''
		if value is None:
			value = 'NULL'
		else:
			value = self._connection.converter.escape(str(value))
			if is_literal:
				value = '"%s"' % value
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