from exceptions.http_base import \
  BadRequestException, \
  MethodNotAllowedException, \
  NotFoundException, \
  AmbiguousPathException, \
  InternalServerError
from util.functions import get_type_name, hash_dict, hash_list_or_tuple
from util.http import HTTPRequestMethods, FormParams, PathParam, HTTPMIMETypes

import re

from os import listdir, path

base_path = path.dirname(__file__).replace('\\', '/')
if len(base_path) > 0 and base_path.rfind('/') > -1:
  base_path = base_path[:base_path.rfind('/')]

def path_param_bool_func(not_a_bool_yet: str) -> bool:
  not_a_bool_yet = not_a_bool_yet.lower()
  
  if not_a_bool_yet == 'true':
    return True
  
  if not_a_bool_yet == 'false':
    return False
  
  raise ValueError('%s couldn\'t be converted to a bool.' % not_a_bool_yet)

class AvailablePath:
  def __init__(self, request_method:str = None, path:str = None, query_params:(list, tuple) = None, path_params:(list, tuple) = None, expected_body:str = None, description:str = None):
    grievances = []
    
    if query_params is not None:
      if not isinstance(query_params, (list, tuple)):
        grievances.append('query_params must be a list or tuple of QueryParams.')
      
      for param in query_params:
        if not isinstance(param, FormParams):
          grievances.append('found a %s in the list of query_params, each of which must be a QueryParam.' % (get_type_name(param), ))
    
    if path_params is not None:
      if not isinstance(query_params, (list, tuple)):
        grievances.append('path_params must be a list or tuple of PathParams.')
      
      for param in path_params:
        if not isinstance(param, PathParam):
          grievances.append('found a %s in the list of path_params, each of which must be a PathParam.' % (get_type_name(param), ))
    
    # gonna trust that i'm the only one using this class and i'm gonna do it right.
    self.request_method = None if request_method is None else request_method.upper()
    self.path = path
    self.query_params = [] if query_params is None else query_params
    self.path_params = [] if path_params is None else path_params
    self.expected_body = expected_body
    self.description = description
  
  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return False
    
    for key in other.__dict__:
      if key not in self.__dict__:
        return False
    
    for key in self.__dict__:
      if not key in other.__dict__:
        return False
      
      if self.__dict__[key] != other.__dict__[key]:
        return False
    
    return True
  
  def __hash__(self):
    result = 0
    
    for val in self.__dict__.values():
      new_hash = 0
      if isinstance(val, dict):
        new_hash = hash_dict(val)
      elif isinstance(val, list):
        new_hash = hash_list_or_tuple(val)
      else:
        new_hash = hash(val)
      
      result = result * 397 ^ new_hash
    
    return result
  
  def __str__(self):
    result = '%s %s' % (self.request_method, self.path)
    
    if len(self.description) > 0:
      result = '%s\n%s' % (result, self.description)
    
    return result

path_var_type_funcs = {'bool': path_param_bool_func, 'float': float, 'int': int, 'str': str}
path_param_folder_name_re = re.compile('^__[a-zA-Z_][a-zA-Z0-9_]*__(bool|float|int|str)__$')
rm_data = None
class PathNode:
  def __init__(self, parent, full_start_path:str, folder_name:str):
    grievances = []
    
    if parent is not None and not isinstance(parent, PathNode):
      grievances.append('a parent path node must be a path node.')
    
    if not isinstance(full_start_path, str):
      grievances.append('a start path must be a string.')
    
    if not isinstance(folder_name, str):
      grievances.append('a folder name must be a string.')
    
    if len(grievances) > 0:
      raise(TypeError('\n'.join(grievances)))
    
    folder_name = folder_name.replace('\\', '/')
    if folder_name[0] == '/':
      folder_name = folder_name[1:]
    if folder_name[-1] == '/':
      folder_name = folder_name[:-1]
    
    if full_start_path[-1] != '/':
      full_start_path += '/'
    
    if not path.exists(full_start_path + folder_name) or not path.isdir(full_start_path + folder_name):
      raise ValueError('"%s" doesn\'t exist or isn\'t a directory.' % (full_start_path + folder_name, ))
    
    self._parent = parent
    self._dir_children = dict()
    self._var_children = dict()
    self._folder_name = folder_name
    self._is_path_param = (path_param_folder_name_re.match(self._folder_name) is not None)
    self._var_name = None
    self._var_type_name = None
    self._var_parse_func = None
    self._request_method_funcs = {rm: None for rm in HTTPRequestMethods}
    self._request_method_help = {rm: None for rm in HTTPRequestMethods}
    self._request_method_allowed_accept_types = {rm: None for rm in HTTPRequestMethods}
    self._request_method_default_content_type = {rm: None for rm in HTTPRequestMethods}
    
    if self._is_path_param:
      var_parts = self._folder_name.split('__')[1:-1]
      self._var_name = '__'.join(var_parts[:-1])
      self._var_type_name = var_parts[-1]
      self._var_parse_func = path_var_type_funcs[var_parts[-1]]
    
    index_path = full_start_path + folder_name + '/index.py'
    if not path.exists(index_path):
      if parent is not None:
        parent.add_child(self)
      return
    
    index_path = (self.get_raw_path()[1:] + '/index.py').replace('/', '.')[:-3]
    for request_method in HTTPRequestMethods:
      # this has to use a global variable because "exec" doesn't work on locals.  this seems very thread-unsafe.
      request_fn_name = str(request_method)
      
      code = \
        'def get_data():\n' \
        '  global rm_data\n' \
        '  try:\n' + \
        '    from %s import %s as the_data\n' % (index_path, request_fn_name) + \
        '  except ImportError as e:\n' \
        '    if not str(e).startswith("cannot import name \'%s\' from \'%s\' "):\n' % (str(request_method), index_path) + \
        '      print("error: %s" % (str(e), ))\n' \
        '      raise e\n' \
        '    \n' \
        '    rm_data = None\n' \
        '    return\n' \
        '  rm_data = the_data\n' \
        'get_data()'
      exec(code)
      
      self._request_method_funcs[request_method] = rm_data
      
      code = \
        'def get_data():\n' + \
        '  global rm_data\n' + \
        '  try:\n' + \
        '    from %s import %s_help as the_data\n' % (index_path, request_fn_name) + \
        '  except ImportError as e:\n' \
        '    if not str(e).startswith("cannot import name \'%s_help\' from \'%s\' "):\n' % (str(request_method), index_path) + \
        '      print("error: %s" % (str(e), ))\n' \
        '      raise e\n' \
        '    \n' \
        '    rm_data = None\n' \
        '    return\n' \
        '  rm_data = the_data\n' \
        'get_data()'
      exec(code)
      
      if rm_data is None or isinstance(rm_data, AvailablePath):
        self._request_method_help[request_method] = rm_data
      else:
        raise TypeError('found a %s for %s %s allowed accept types.' % (get_type_name(rm_data), request_fn_name.upper(), full_start_path + folder_name))
      
      code = \
        'def get_data():\n' + \
        '  global rm_data\n' + \
        '  try:\n' + \
        '    from %s import %s_allowed_accept_types as the_data\n' % (index_path, request_fn_name) + \
        '  except ImportError as e:\n' \
        '    if not str(e).startswith("cannot import name \'%s_allowed_accept_types\' from \'%s\' "):\n' % (str(request_method), index_path) + \
        '      print("error: %s" % (str(e), ))\n' \
        '      raise e\n' \
        '    \n' \
        '    rm_data = None\n' \
        '    return\n' \
        '  rm_data = the_data\n' \
        'get_data()'
      exec(code)
      
      if rm_data is None or isinstance(rm_data, set):
        self._request_method_allowed_accept_types[request_method] = rm_data
      else:
        raise TypeError('found a %s for %s %s allowed accept types.' % (get_type_name(rm_data), request_fn_name.upper(), full_start_path + folder_name))
      
      code = \
        'def get_data():\n' + \
        '  global rm_data\n' + \
        '  try:\n' + \
        '    from %s import %s_default_content_type as the_data\n' % (index_path, request_fn_name) + \
        '  except ImportError as e:\n' \
        '    if not str(e).startswith("cannot import name \'%s_default_content_type\' from \'%s\' "):\n' % (str(request_method), index_path) + \
        '      print("error: %s" % (str(e), ))\n' \
        '      raise e\n' \
        '    \n' \
        '    rm_data = None\n' \
        '    return\n' \
        '  rm_data = the_data\n' \
        'get_data()'
      exec(code)
      
      if rm_data is None or isinstance(rm_data, HTTPMIMETypes):
        self._request_method_default_content_type[request_method] = rm_data
      else:
        raise TypeError('found a %s for %s %s default content type.' % (get_type_name(rm_data), request_fn_name.upper(), full_start_path + folder_name))
      
      if self._request_method_funcs[request_method] is not None:
        missing_data = []
        error = False
        
        if self._request_method_allowed_accept_types[request_method] is None:
          error = True
          missing_data.append('allowed accept types')
        
        if self._request_method_default_content_type[request_method] is None:
          error = True
          missing_data.append('default content type')
        
        if error:
          raise ValueError('missing %s for %s %s' % (' and '.join(missing_data), request_fn_name.upper(), full_start_path + folder_name))
    
    if parent is not None:
      parent.add_child(self)
  
  def __eq__(self, other) -> bool:
    return isinstance(other, PathNode) and \
      self._parent == other._parent and \
      self._folder_name == other._folder_name
  
  def __getitem__(self, key:(str, HTTPRequestMethods)):
    if isinstance(key, HTTPRequestMethods):
      if key in self._request_method_funcs:
        return self._request_method_funcs[key], self._request_method_help.get(key, None)
      
      raise MethodNotAllowedException(str(key).upper(), self.get_pretty_path())
    
    if key in self._dir_children and key in self._var_children:
      raise KeyError('ambiguous key; a dir and a path var are both named "%s".' % (key, ))
    
    if key in self._dir_children:
      return self._dir_children.__getitem__(key)
    
    if key in self._var_children:
      return self._var_children.__getitem__(key)
    
    raise KeyError('no dir or var named "%s" exists as a child of this node.' % (key,))
  
  def __hash__(self) -> int:
    return (hash(self._parent)*397) ^ hash(self._folder_name)
  
  def __iadd__(self, other):
    if not isinstance(other, PathNode):
      raise TypeError('only PathNodes can be added to PathNodes (as children).')
  
    self.add_child(other)
    return self
  
  def __iter__(self):
    return self.get_children().__iter__()
  
  def __str__(self) -> str:
    return self.get_pretty_path()
  
  def get_parent(self):
    return self._parent
  
  def get_children(self) -> set:
    return set(self._dir_children.values()) | set(self._var_children.values())
  
  def get_dir_child(self, dir_name:str):
    return self._dir_children[dir_name]
  
  def get_dir_children(self):
    return self._dir_children
  
  def get_var_child(self, var_name:str):
    return self._var_children[var_name]
  
  def get_var_children(self):
    return self._var_children
  
  def add_child(self, child) -> None:
    if not isinstance(child, PathNode):
      raise TypeError('a PathNode child must be a PathNode.')
    
    if child.is_path_param():
      self._var_children[child.get_var_name()] = child
      return
    
    self._dir_children[child.get_raw_folder_name()] = child
  
  def get_raw_folder_name(self) -> str:
    return self._folder_name
  
  def get_raw_path(self) -> str:
    result = ''
    
    node = self
    while node is not None:
      result = "/%s%s" % (node.get_raw_folder_name(), result)
      node = node._parent
    
    return result
  
  def get_pretty_folder_name(self) -> str:
    if path_param_folder_name_re.match(self._folder_name) is None:
      return self._folder_name
    
    return '{%s (%s)}' % (self._var_name, self._var_type_name)
  
  def get_pretty_path(self) -> str:
    result = ''
    
    node = self
    while node is not None:
      result = "/%s%s" % (node.get_pretty_folder_name(), result)
      node = node._parent
    
    return result
  
  def get_request_method_func(self, request_method:HTTPRequestMethods) -> callable:
    return self._request_method_funcs.get(request_method, None)
  
  def get_request_method_help(self, request_method:HTTPRequestMethods) -> AvailablePath:
    return self._request_method_help.get(request_method, None)
  
  def get_request_method_allowed_content_types(self, request_method:HTTPRequestMethods) -> set:
    return self._request_method_allowed_accept_types.get(request_method, None)
  
  def get_request_method_default_content_type(self, request_method:HTTPRequestMethods) -> HTTPMIMETypes:
    return self._request_method_default_content_type.get(request_method, None)
  
  def is_path_param(self) -> bool:
    return self._is_path_param
  
  def can_match(self, val:str) -> bool:
    if self._is_path_param:
      try:
        self.parse(val)
        return True
      except ValueError:
        return False
    
    return self.get_raw_folder_name() == val
  
  def get_var_name(self) -> str:
    if not self._is_path_param:
      raise ValueError('this isn\'t a path param node.')
    
    return self._var_name
  
  def get_var_type_name(self) -> str:
    if not self._is_path_param:
      raise ValueError('this isn\'t a path param node.')
    
    return self._var_type_name
  
  def parse(self, val:str):
    if not self.is_path_param():
      raise TypeError('this isn\'t a path param folder.')
    
    if not isinstance(val, str):
      raise TypeError('a value to parse must be a string (part of a relative path).')
    
    return self._var_parse_func(val)

default_interface_dir = 'interface'
valid_path_re = re.compile('^[/a-zA-Z0-9 _+%.]+$')
rel_path_not_found_error = 'the path "%s" wasn\'t found.'
def get_path_trie(start_path:str = default_interface_dir) -> PathNode:
  if start_path[0] == '/':
    start_path = start_path[1:]
  
  if start_path[-1] == '/':
    start_path = start_path[:-1]
  
  base_folder = base_path
  if base_folder[-1] == '/':
    base_folder = base_folder[:-1]
  
  root_node = PathNode(None, base_folder, start_path)
  
  nodes_to_process = [root_node]
  while len(nodes_to_process) > 0:
    current_node = nodes_to_process.pop(0)
    
    for subdir in listdir(base_folder + current_node.get_raw_path()):
      if subdir == '__pycache__' or not path.isdir(base_folder + current_node.get_raw_path() + '/' + subdir):
        continue
      
      child_node = PathNode(current_node, base_path + current_node.get_raw_path(), subdir)
      current_node += child_node
      nodes_to_process.append(child_node)
  
  return root_node

class PathData:
  def __init__(self, path_node:PathNode, path_parameters:dict, error_message:str):
    self.path_parameters = path_parameters
    self.error_message = error_message
    self.path_node = path_node
  
  def __add__(self, other):
    if isinstance(other, PathNode):
      if self.path_node != other.get_parent():
        raise ValueError('choose one of this data\'s children.')
      
      return PathData(other, self.path_parameters, self.error_message)
    
    if isinstance(other, dict):
      return PathData(self.path_node, self.path_parameters | other, self.error_message)
    
    if isinstance(other, PathData):
      if self.path_node != other.path_node.get_parent():
        raise ValueError('choose one of this data\'s children.')
      
      error_message = self.error_message
      if other.error_message is not None:
        if error_message is None:
          error_message = other.error_message
        else:
          error_message += '\n' + other.error_message
      return PathData(other.path_node, self.path_parameters | other.path_parameters, error_message)
    
    raise TypeError('a PathData can only be added to a PathNode, a dict or a PathData.')
  
  def __eq__(self, other) -> bool:
    return isinstance(other, PathData) and \
      self.path_node == other.path_node and \
      self.path_parameters == other.path_parameters and \
      self.error_message == other.error_message
  
  def __hash__(self) -> int:
    return (((hash(self.path_node)*397) ^ hash_dict(self.path_parameters))*397) ^ hash(self.error_message)
  
  def __iadd__(self, other):
    if isinstance(other, PathNode):
      if self.path_node != other.get_parent():
        raise ValueError('choose one of this data\'s children.')
      
      self.path_node = other
    elif isinstance(other, dict):
      self.path_parameters |= other
    elif isinstance(other, PathData):
      if self.path_node != other.path_node.get_parent():
        raise ValueError('choose one of this data\'s children.')
      
      self.path_node = other.path_node
      self.path_parameters |= other.path_parameters
      
      if other.error_message is not None:
        if self.error_message is None:
          self.error_message = other.error_message
        else:
          self.error_message += '\n' + other.error_message
    else:
      raise TypeError('only a PathNode, a dict or a PathData can be added to a PathData.')
    
    return self

end_path = '/index.py'
path_tries = {default_interface_dir: get_path_trie(default_interface_dir)}
def get_and_validate_rel_path(environment:dict, start_path:str = default_interface_dir) -> PathData:
  query_string = environment['QUERY_STRING']
  rel_path = environment['REQUEST_URI']
  if len(query_string) > 0:
    rel_path = rel_path[:-1 * (len(query_string) + 1)]
  
  rel_path = rel_path.replace('\\', '/')
  if len(rel_path) > 0:
    if rel_path[-1] == '?':
      rel_path = rel_path[:-1]
    
    if rel_path[0] == '/':
      rel_path = rel_path[1:]
    if len(rel_path) > 0 and rel_path[-1] == '/':
      rel_path = rel_path[:-1]
  
  if start_path not in path_tries:
    path_tries[start_path] = get_path_trie(start_path)
  
  root_path_data = PathData(path_tries[start_path], {}, None)
  
  if len(rel_path) == 0:
    return root_path_data
  
  incoming_pieces = rel_path.split('/')
  old_paths = {root_path_data}
  for rel_dir in incoming_pieces:
    new_paths = set()
    for path_data in old_paths:
      for subdir_node in path_data.path_node.get_children():
        if not subdir_node.is_path_param():
          if not subdir_node.can_match(rel_dir):
            continue
          
          new_data = path_data + subdir_node
          new_paths.add(new_data)
          continue
        
        var_val = None
        error_message = None
        try:
          var_val = subdir_node.parse(rel_dir)
        except ValueError:
          n_or_not = 'n' if subdir_node.get_var_type_name() == 'int' else ''
          error_message = 'couldn\'t parse a%s %s from "%s" for %s.' % (n_or_not, subdir_node.get_var_type_name(), rel_dir, subdir_node.get_var_name())
        
        new_data = path_data + subdir_node + {subdir_node.get_var_name(): var_val}
        if new_data.error_message is None:
          new_data.error_message = error_message
        elif error_message is not None:
          new_data.error_message += '\n%s' % error_message
        
        new_paths.add(new_data)
    
    old_paths = new_paths
    
    if len(old_paths) == 0:
      break
  
  if len(old_paths) == 0:
    raise NotFoundException(rel_path_not_found_error % (rel_path,))
  
  if len(old_paths) == 1:
    path_data = old_paths.pop()
    if path_data.error_message is not None:
      raise BadRequestException(path_data.error_message)
    
    if not path.exists(base_path + path_data.path_node.get_raw_path() + end_path):
      raise NotFoundException(rel_path_not_found_error % (rel_path,))
    
    return path_data
  
  bad_path_param_paths = set()
  good_paths = set()
  for path_data in old_paths:
    if path_data.error_message is not None:
      bad_path_param_paths.add(path_data)
    elif path.exists(base_path + path_data.path_node.get_raw_path() + end_path):
      good_paths.add(path_data)
  
  if len(good_paths) == 0:
    if len(bad_path_param_paths) > 1:
      raise BadRequestException('multiple request paths matched the input, but each one had an invalid variable value:\n' + \
                                '\n'.join({path_data.error_message for path_data in bad_path_param_paths}))
    elif len(bad_path_param_paths) == 1:
      raise BadRequestException(bad_path_param_paths.pop().error_message)
    else:
      raise NotFoundException(rel_path_not_found_error % (rel_path,))
  
  if len(good_paths) == 1:
    return good_paths.pop()
  
  if len(good_paths) > 1:
    raise AmbiguousPathException([good_path.path_node.get_raw_path() for good_path in good_paths])
  
  raise InternalServerError('got a negative number of paths.')