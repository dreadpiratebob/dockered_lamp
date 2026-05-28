from exceptions.http_base import BadRequestException
from util.functions import get_type_name, hash_dict, hash_list_or_tuple

from enum import Enum
from types import FunctionType

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
    self.type_name = name
    self.parent = parent
  
  def __eq__(self, other) -> bool:
    return isinstance(other, type(self)) and \
      self.type_name == other.type_name and \
      self.parent == other.parent
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    return hash((self.type_name, self.parent))
  
  def __repr__(self) -> str:
    return str(self)
  
  def __str__(self) -> str:
    return '%s/%s' % (self.parent.value, self.type_name)
  
  CSS    = 'css',    MajorHTTPMIMETypes.TEXT
  FLAC   = 'flac',   MajorHTTPMIMETypes.AUDIO
  JSON   = 'json',   MajorHTTPMIMETypes.APPLICATION
  MPEG   = 'mpeg',   MajorHTTPMIMETypes.AUDIO
  PLAIN  = 'plain',  MajorHTTPMIMETypes.TEXT
  STAR   = '*',      MajorHTTPMIMETypes.STAR
  X_YAML = 'x-yaml', MajorHTTPMIMETypes.APPLICATION
  XML    = 'xml',    MajorHTTPMIMETypes.APPLICATION
  YAML   = 'yaml',   MajorHTTPMIMETypes.APPLICATION
minor_http_mime_types_by_name = {mime_type.type_name: mime_type for mime_type in MinorHTTPMIMETypes}

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
HTTPMIMETypes_by_name = {str(x): x for x in HTTPMIMETypes}

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

_bearer_prefix = 'Bearer '
def get_authorization_header_value(value:str) -> str:
  if value is None:
    return None
  
  if not isinstance(value, str):
    raise BadRequestException('an authorization header value must be a string.')
  
  if value[0:len(_bearer_prefix)] == _bearer_prefix:
    return value[len(_bearer_prefix):]
  
  return value

_range_header_prefix = 'range: '
def _parse_range_header(header:str) -> HTTPRange:
  if not isinstance(header, str):
    raise TypeError('a range header value can only be parsed from a string.')
  
  header = header.lower()
  
  if header.startswith(_range_header_prefix):
    header = header[len(_range_header_prefix):]
  
  header = header.split('=')
  unit = header[0]
  
  ranges = []
  tokens = header[1].split(', ')
  invalid_values = []
  for token in tokens:
    token = token.split('-')
    
    start = token[0]
    if len(start) == 0:
      start = None
    else:
      try:
        start = int(start)
      except ValueError:
        invalid_values.append(token[0])
    
    end = token[1]
    if len(end) == 0:
      end = None
    else:
      try:
        end = int(end)
      except ValueError:
        invalid_values.append(token[1])
    
    ranges.append((start, end))
  
  if len(invalid_values) > 0:
    raise BadRequestException('invalid range values: %s' % ', '.join(invalid_values))
  
  return HTTPRange(unit, ranges)

class HTTPHeaders(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, header_name:str, other_names:set[str], get_value:FunctionType, default_value):
    self._header_name = header_name
    self._other_names = other_names
    self._get_value = get_value
    self._default_value = default_value
  
  def __hash__(self) -> int:
    return hash(self._header_name)
  
  def __eq__(self, other:any) -> bool:
    return isinstance(other, type(self)) and \
      self._header_name == other._header_name
  
  def __ge__(self, other) -> bool:
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name >= other._header_name
  
  def __gt__(self, other) -> bool:
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name > other._header_name
  
  def __le__(self, other) -> bool:
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name <= other._header_name
  
  def __lt__(self, other) -> bool:
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name < other._header_name
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __repr__(self) -> str:
    return 'http header (%s)' % (self._header_name, )
  
  def __str__(self) -> str:
    return self._header_name
  
  def get_value(self, environment:dict) -> any:
    for name in {self._header_name} | self._other_names:
      if name in environment:
        return self._get_value(environment[name])
    
    return self.default_value()
  
  def default_value(self) -> str:
    return self._default_value
  
  ACCEPT = 'accept', {'HTTP_ACCEPT'}, lambda value: HTTPMIMETypes_by_name.get(value, HTTPMIMETypes.APPLICATION_YAML), HTTPMIMETypes.APPLICATION_YAML
  AUTHORIZATION = 'authorization', {'Authorization', 'HTTP_AUTHORIZATION'}, get_authorization_header_value, None
  CONTENT_TYPE = 'content-type', {'Content-Type', 'CONTENT_TYPE'}, lambda value: HTTPMIMETypes_by_name.get(value, HTTPMIMETypes.APPLICATION_YAML), HTTPMIMETypes.APPLICATION_YAML
  RANGE = 'range', {'HTTP_RANGE'}, _parse_range_header, None

class HTTPStatusCodes(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, code:int, message:str):
    self._code = code
    self._message = message
  
  def __hash__(self) -> int:
    return hash(self._code)
  
  def __eq__(self, other:any) -> bool:
    return isinstance(other, HTTPStatusCodes) and \
      self._code == other._code
  
  def __ne__(self, other:any) -> bool:
    return not self.__eq__(other)
  
  def __repr__(self) -> str:
    return 'http status code (%s %s)' % (self._code, self._message)
  
  def __str__(self) -> str:
    return str(self._code) + ' ' + self._message
  
  def get_code(self):
    return self._code
  
  def get_message(self):
    return self._message
  
  HTTP100 = 100, 'Continue'
  HTTP102 = 102, 'Processing'
  HTTP103 = 103, 'Early Hints'
  HTTP200 = 200, 'OK'
  HTTP201 = 201, 'Created'
  HTTP202 = 202, 'Accepted'
  HTTP203 = 203, 'Non-Authoritative Information'
  HTTP204 = 204, 'No Content'
  HTTP205 = 205, 'Reset Content'
  HTTP206 = 206, 'Partial Content'
  HTTP207 = 207, 'Multi-Status'
  HTTP208 = 208, 'Already Reported'
  HTTP218 = 218, 'This is fine'
  HTTP226 = 226, 'IM Used'
  HTTP300 = 300, 'Multiple Choices'
  HTTP301 = 301, 'Moved Permanently'
  HTTP302 = 302, 'Found'
  HTTP303 = 303, 'See Other'
  HTTP304 = 304, 'Not Modified'
  HTTP305 = 305, 'Use Proxy'
  HTTP306 = 306, 'Switch Proxy'
  HTTP307 = 307, 'Temporary Redirect'
  HTTP308 = 308, 'Permanent Redirect'
  HTTP400 = 400, 'Bad Request'
  HTTP401 = 401, 'Unauthorized'
  HTTP402 = 402, 'Payment Required'
  HTTP403 = 403, 'Forbidden'
  HTTP404 = 404, 'Not Found'
  HTTP405 = 405, 'Method Not Allowed'
  HTTP406 = 406, 'Not Acceptable'
  HTTP407 = 407, 'Proxy Authentication Required'
  HTTP408 = 408, 'Request Timeout'
  HTTP409 = 409, 'Conflict'
  HTTP410 = 410, 'Gone'
  HTTP411 = 411, 'Length Required'
  HTTP412 = 412, 'Precondition Failed'
  HTTP413 = 413, 'Payload Too Large'
  HTTP414 = 414, 'URI Too Long'
  HTTP415 = 415, 'Unsupported Media Type'
  HTTP416 = 416, 'Range Not Satisfiable'
  HTTP417 = 417, 'Expectation Failed'
  HTTP418 = 418, 'I\'m a teapot'
  HTTP421 = 421, 'Misdirected Request'
  HTTP422 = 422, 'Unprocessable Entity'
  HTTP423 = 423, 'Locked'
  HTTP424 = 424, 'Failed Dependency'
  HTTP425 = 425, 'Too Early'
  HTTP426 = 426, 'Upgrade Required'
  HTTP428 = 428, 'Precondition Required'
  HTTP429 = 429, 'Too Many Requests'
  HTTP431 = 431, 'Request Header Fields Too Large'
  HTTP451 = 451, 'Unavailable For Legal Reasons'
  HTTP500 = 500, 'Internal Server Error'
  HTTP501 = 501, 'Not Implemented'
  HTTP502 = 502, 'Bad Gateway'
  HTTP503 = 503, 'Service Unavailable'
  HTTP504 = 504, 'Gateway Timeout'
  HTTP505 = 505, 'HTTP Version Not Supported'
  HTTP506 = 506, 'Variant Also Negotiates'
  HTTP507 = 507, 'Insufficient Storage'
  HTTP508 = 508, 'Loop Detected'
  HTTP510 = 510, 'Not Extended'
  HTTP511 = 511, 'Network Authentication Required'
HTTPStatusCodes_by_code = {sc.get_code(): sc for sc in HTTPStatusCodes}

class HTTPRequestMethods(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, name:str):
    self._name = name
  
  def __eq__(self, other:any) -> bool:
    return isinstance(other, HTTPRequestMethods) and self._name == other._name
  
  def __ne__(self, other:any) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    return hash(self._name)
  
  def __repr__(self) -> str:
    return 'http request method (%s)' % (self._name, )
  
  def __str__(self) -> str:
    return self._name
  
  DELETE  = 'delete'
  GET     = 'get'
  OPTIONS = 'options'
  PATCH   = 'patch'
  POST    = 'post'
  PUT     = 'put'
HTTPRequestMethods_by_name = {rm.name.lower(): rm for rm in HTTPRequestMethods} | {rm.name.upper(): rm for rm in HTTPRequestMethods}

class Message:
  def __init__(self, message:str):
    self.message = message
  
  def __eq__(self, other:any) -> bool:
    if not isinstance(other, Message):
      return False
    
    return self.message == other.message
  
  def __ne__(self, other:any) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    return hash(self.message)
  
  def __add__(self, other:any):
    if isinstance(other, Message):
      return Message(self.message + other.message)
    elif isinstance(other, str):
      return Message(self.message + other)
    else:
      raise TypeError('can only add messages or strings to messages.')
  
  def __iadd__(self, other:any) -> None:
    if isinstance(other, Message):
      self.message += other.message
    elif isinstance(other, str):
      self.message += other
    else:
      raise TypeError('can only add messages or strings to messages.')
  
  def __repr__(self) -> str:
    return 'message(%s)' % (self.message, )
  
  def __str__(self) -> str:
    return self.message

class Response:
  def __init__(self, payload:any, status_code:HTTPStatusCodes, mime_type:HTTPMIMETypes = None, serialization_falls_back_to_fields:bool = True, use_public_fields_only:bool = True, use_base_field_in_xml:bool = False, use_base_field_in_yaml:bool = False, data_is_raw:bool = False, content_length:int = None, headers:dict[str, str] = None):
    grievances = []
    
    if not isinstance(status_code, HTTPStatusCodes):
      grievances.append('a status_code must be an HTTPStatusCode.')
    
    if mime_type is not None and not isinstance(mime_type, HTTPMIMETypes):
      grievances.append('a mime type must be an HTTPMIMEType.')
    
    if not isinstance(serialization_falls_back_to_fields, bool):
      grievances.append('the "fall back to fields" flag must be a bool.')
    
    if not isinstance(use_public_fields_only, bool):
      grievances.append('the "use public fields only" flag must be a bool.')
    
    if not isinstance(use_base_field_in_xml, bool):
      grievances.append('the "use base field in xml" flag must be a bool.')
    
    if not isinstance(use_base_field_in_yaml, bool):
      grievances.append('the "use base field in yaml" flag must be a bool.')
    
    if not isinstance(data_is_raw, bool):
      grievances.append('the "data is raw" flag must be a bool.')
    
    if content_length is not None and not isinstance(content_length, int):
      grievances.append('a content\'s length must be an int.')
    
    if headers is None:
      headers = dict()
    elif isinstance(headers, dict):
      for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
          grievances.append('a header\'s name and value must be a string.')
          break
    else:
      grievances.append('headers must be a dict.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    self.payload = payload
    self._status_code = status_code
    self._mime_type = mime_type
    self._fall_back_to_fields = serialization_falls_back_to_fields
    self._use_public_fields_only = use_public_fields_only
    self._use_base_field_in_xml = use_base_field_in_xml
    self._use_base_field_in_yaml = use_base_field_in_yaml
    self._data_is_raw = data_is_raw
    self._content_length = content_length
    self._headers = headers
  
  def get_status_code(self) -> HTTPStatusCodes:
    return self._status_code
  
  def get_mime_type(self) -> HTTPMIMETypes:
    return self._mime_type
  
  def set_mime_type(self, mime_type:HTTPMIMETypes) -> None:
    if not isinstance(mime_type, HTTPMIMETypes):
      raise TypeError('a mime type must be an HTTPMIMEType.')
    
    self._mime_type = mime_type
  
  def data_is_raw(self) -> bool:
    return self._data_is_raw
  
  def get_headers(self) -> dict:
    return self._headers
  
  def upsert_headers(self, headers:dict[str, str]) -> None:
    if not isinstance(headers, dict):
      raise TypeError('headers must be a dict[str, str].')
    
    if self._headers is None:
      self._headers = dict()
    
    for key, value in headers.items():
      if not isinstance(key, str) or not isinstance(value, str):
        raise TypeError('headers must be a dict[str, str].')
    
    for key, value in headers.items():
      self._headers[key] = value
  
  def get_content_length(self) -> int:
    return self._content_length
  
  def serialization_falls_back_to_fields(self) -> bool:
    return self._fall_back_to_fields
  
  def use_public_fields_only(self) -> bool:
    return self._use_public_fields_only
  
  def use_base_field_in_xml(self) -> bool:
    return self._use_base_field_in_xml
  
  def use_base_field_in_yaml(self) -> bool:
    return self._use_base_field_in_yaml