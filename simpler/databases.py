from MySQLdb import Connection

class MySQL:
	client = None
	cursor = None

	def __init__(self, autocommit=True, *args, **kwargs) -> None:
		''' Creates a MySQL database adapter with a handful of recurrent functions. '''
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