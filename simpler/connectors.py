from typing import Union
from pandas import ExcelFile, read_excel, DataFrame, concat
from numpy import arange, concatenate, array
from re import compile, IGNORECASE

class MySQL:
	client = None
	cursor = None

	def __init__(self, autocommit: bool = True, *args, **kwargs) -> None:
		''' Creates a MySQL database adapter with a handful of recurrent functions. '''
		try:
			from MySQLdb import Connection
		except:
			raise RuntimeError('Install MySQL or MariaDB and then do "pip install mysqlclient" to use this connector.')
		self.connection = Connection(*args, **kwargs)
		self.connection.autocommit(autocommit)
		self.cursor = self.connection.cursor()

	def close(self) -> None:
		''' Closes the current cursor and connection. '''
		self.cursor.close()
		self.connection.close()

	def find_many(self, query: str, *params: tuple) -> list:
		''' Returns a list of {column_name: value} dicts of the selected rows. '''
		assert 'select' in query.lower()
		self.cursor.execute(query, params)
		return [
			{k[0]: v for k, v in zip(self.cursor.description, row)}
			for row in self.cursor.fetchall()
		]

	def find_one(self, query: str, *params: tuple) -> dict:
		''' Returns a {column_name: value} dict of the first selected row. '''
		assert 'select' in query.lower()
		self.cursor.execute(query, params)
		row = self.cursor.fetchone()
		if row is not None:
			row = {k[0]: v for k, v in zip(self.cursor.description, row)}
		return row

	def find_column(self, query: str, *params: tuple) -> str:
		''' Returns the value of the first attribute of a selected row. '''
		assert 'select' in query.lower()
		self.cursor.execute(query, params)
		res = self.cursor.fetchone()
		if res:
			return res[0]

	def insert(self, query: str, *params: tuple) -> int:
		''' Inserts a row and returns the id of the last one inserted. '''
		assert 'insert' in query.lower()
		self.cursor.execute(query, params)
		return int(self.cursor.lastrowid)

	def apply(self, query: str, *params: tuple) -> int:
		''' Executes an update or delete operation and returns the number of rows affected. '''
		assert 'update' in query.lower() or 'delete' in query.lower()
		self.cursor.execute(query, params)
		return int(self.cursor.rowcount)

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