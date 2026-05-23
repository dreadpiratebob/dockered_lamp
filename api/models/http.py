from enum import Enum

from exceptions.http_base import BadRequestException
from util.functions import get_type_name, hash_dict, hash_list_or_tuple

class AvailablePath:
  def __init__(self, request_method:str = None, path:str = None, query_params:(list, tuple) = None, path_params:(list, tuple) = None, expected_body:str = None, description:str = None):
    grievances = []
    
    if query_params is not None:
      if not isinstance(query_params, (list, tuple)):
        grievances.append('query_params must be a list or tuple of QueryParams.')
      
      for param in query_params:
        if not isinstance(param, FormParams):
          grievances.append('found a %s in the list of query_params, each of which must be a QueryParam.' % (get_type_name(param),))
    
    if path_params is not None:
      if not isinstance(query_params, (list, tuple)):
        grievances.append('path_params must be a list or tuple of PathParams.')
      
      for param in path_params:
        if not isinstance(param, PathParams):
          grievances.append('found a %s in the list of path_params, each of which must be a PathParam.' % (get_type_name(param),))
    
    # gonna trust that i'm the only one using this class and i'm gonna do it right.
    self.request_method = None if request_method is None else request_method.upper()
    self.path = path
    self.query_params = [] if query_params is None else query_params
    self.path_params = [] if path_params is None else path_params
    self.expected_body = expected_body
    self.description = description
  
  def __eq__(self, other) -> bool:
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
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
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
  
  def __str__(self) -> str:
    result = '%s %s' % (self.request_method, self.path)
    
    if len(self.description) > 0:
      result = '%s\n%s' % (result, self.description)
    
    return result

class MajorHTTPMIMETypes(Enum):
  APPLICATION = 'application'
  AUDIO = 'audio'
  STAR = '*'
  TEXT = 'text'
major_http_mime_types_by_name = {mime_type.value:mime_type for mime_type in MajorHTTPMIMETypes}

class MinorHTTPMIMETypes(Enum):
  def __init__(self, name:str, parent:MajorHTTPMIMETypes):
    self.name = name
    self.parent = parent
  
  def __eq__(self, other) -> bool:
    return isinstance(other, type(self)) and \
      self.name == other.name and \
      self.parent == other.parent
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    return hash((self.name, self.parent))
  
  def __repr__(self) -> str:
    return str(self)
  
  def __str__(self) -> str:
    return '%s/%s' % (self.parent.value, self.name)
  
  CSS    = 'css',    MajorHTTPMIMETypes.TEXT
  FLAC   = 'flac',   MajorHTTPMIMETypes.AUDIO
  JSON   = 'json',   MajorHTTPMIMETypes.APPLICATION
  MPEG   = 'mpeg',   MajorHTTPMIMETypes.AUDIO
  PLAIN  = 'plain',  MajorHTTPMIMETypes.TEXT
  STAR   = '*',      MajorHTTPMIMETypes.STAR
  X_YAML = 'x-yaml', MajorHTTPMIMETypes.APPLICATION
  XML    = 'xml',    MajorHTTPMIMETypes.APPLICATION
  YAML   = 'yaml',   MajorHTTPMIMETypes.APPLICATION
minor_http_mime_types_by_name = {mime_type.name: mime_type for mime_type in MinorHTTPMIMETypes}

class HTTPMIMETypes(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, http_name:str, serializer_function_name:str, base_structure:[bytes, str]):
    name_tokens = http_name.split('/')
    self.major_type = major_http_mime_types_by_name[name_tokens[0]]
    self.minor_type = minor_http_mime_types_by_name[name_tokens[1]]
    
    self.serializer_function_name = serializer_function_name
    self.base_structure = base_structure
  
  def __eq__(self, other) -> bool:
    return isinstance(other, HTTPMIMETypes) and \
      self.major_type == other.major_type and \
      self.minor_type == other.minor_type and \
      self.serializer_function_name == other.serializer_function_name and \
      self.base_structure == other.base_structure
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    return ((((hash(self.major_type) * 397) ^ hash(self.minor_type) * 397) ^ hash(self.serializer_function_name)) * 397) ^ hash(self.base_structure)
  
  def __str__(self) -> str:
    return '%s/%s' % (self.major_type.value, self.minor_type.value)
  
  APPLICATION_JSON = 'application/json', 'to_json', '{"data": "%s"}'
  APPLICATION_X_YAML = 'application/x-yaml', 'to_yaml', 'data: %s'
  APPLICATION_XML = 'application/xml', 'to_xml', '<data>%s</data>'
  APPLICATION_YAML = 'application/yaml', 'to_yaml', 'data: %s'
  MEDIA_FLAC = 'audio/flac', None, bytes()
  MEDIA_MPEG = 'audio/mpeg', None, bytes()
  STAR_STAR = '*/*', None, bytes()
  TEXT_CSS = 'text/css', None, '%s'
  TEXT_PLAIN = 'text/plain', None, '%s'

class EndpointData:
  def __init__(self, func:callable, endpoint_help:AvailablePath, allowed_content_types:set[HTTPMIMETypes], default_content_type:HTTPMIMETypes):
    missing_data = []
    
    if func is None:
      missing_data.append('a callable function')
    
    if allowed_content_types is None:
      missing_data.append('allowed content types')
    
    if default_content_type is None:
      missing_data.append('a default content type')
    
    if len(missing_data) > 0:
      raise ValueError('missing data: %s' % ', '.join(missing_data))
    
    self.func = func
    self.help = endpoint_help
    self.allowed_content_types = allowed_content_types
    self.default_content_type = default_content_type

class HTTPRange:
  def __init__(self, unit:str, ranges:list[tuple[int, int]]) -> None:
    self.unit = unit
    self.ranges = []
    
    invalid_values = []
    for range in ranges:
      begin = range[0]
      if begin is not None and not isinstance(begin, int):
        invalid_values.append(begin)
      
      end = range[1]
      if end is not None and not isinstance(end, int):
        invalid_values.append(end)
      
      self.ranges.append((begin, end))
    
    if len(invalid_values) > 0:
      raise ValueError('invalid byte values: %s' % ', '.join([str(val) for val in invalid_values]))
  
  def __len__(self) -> int:
    result = 0
    
    for r in self.ranges:
      if not isinstance(r[1], int):
        return None
      
      if not isinstance(r[0], int):
        result += r[1]
        continue
      
      result += r[1] - r[0]
    
    return result
  
  def __str__(self) -> str:
    result = '%s=' % self.unit
    
    for range in self.ranges:
      result += '%s-%s' % (range[0], range[1])
    
    return result

class FormParams(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, param_name:str, required:bool, parse_func, public_param_type_name:str, exception_param_type_name:str, default_value, description:str):
    self.param_name = param_name
    self.is_required = required
    self._parse_func = parse_func
    self.param_type = public_param_type_name
    self._exception_param_type_name = exception_param_type_name
    self.default_value = default_value
    self.description = description
  
  def __str__(self):
    return self.param_name + ' (' + ('required' if self.is_required else 'optional') + '): ' + self.description
  
  def get_value(self, params:dict, return_error_message:bool = True):
    return get_param(self.param_name, params, self._parse_func, self._exception_param_type_name, self.is_required, 'query', self.default_value, return_error_message)

class PathParams(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, param_name:str, public_param_type_name:str, param_type_name_for_exceptions:str, description:str, parse_func):
    self.param_name = param_name
    self.param_type = public_param_type_name
    self._param_type_name_for_exceptions = param_type_name_for_exceptions
    self.description = description
    self._parse_func = parse_func
  
  def __str__(self):
    return self.param_name
  
  def get_value(self, path_params:dict[str, str], return_error_message = True):
    return get_param(self.param_name, path_params, self._parse_func, self._param_type_name_for_exceptions, True, 'path', None, return_error_message)

def get_param(key:str, params:dict, parser:callable, type_name:str, required:bool = False, param_type:str = 'query', default_value:any=None, return_error_message:bool = False) -> any:
  if key not in params:
    if required:
      if return_error_message:
        return default_value, BadRequestException('the %s parameter called "%s" is required and was missing.' % (param_type, key))
      else:
        raise BadRequestException('the %s parameter called "%s" is required and was missing.' % (param_type, key))
    
    return default_value, None
  
  try:
    return parser(params[key]), None
  except ValueError:
    if return_error_message:
      return default_value, BadRequestException('the %s "%s" couldn\'t be parsed as %s.' % (key, params[key], type_name))
    else:
      raise BadRequestException('the %s "%s" couldn\'t be parsed as %s.' % (key, params[key], type_name))