from importlib.util import spec_from_file_location, module_from_spec
from os.path import exists

def import_from_path(path: str, name: str, module_name: str = '.') -> object:
	''' Loads the script at the specified path and returns an object given its name. '''
	assert exists(path), 'Path "%s" is not valid' % path
	spec = spec_from_file_location(module_name, path)
	module = module_from_spec(spec)
	spec.loader.exec_module(module)
	assert name in module.__dict__, 'Name "%s" in path "%s" does not exist.' % (name, path)
	return module.__dict__[name]