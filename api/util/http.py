from exceptions.http_base import BaseHTTPException, BadRequestException
from models.http import HTTPRange
from util.functions import get_type_name, is_primitive
from util.logger import log_exception

from enum import Enum
from inspect import signature
from types import FunctionType
from urllib.parse import quote_plus

class MajorHTTPMIMETypes(Enum):
  APPLICATION = 'application'
  AUDIO = 'audio'
  STAR = '*'
  TEXT = 'text'
major_http_mime_types_by_name = {mime_type.value: mime_type for mime_type in MajorHTTPMIMETypes}

class MinorHTTPMIMETypes(Enum):
  FLAC = 'flac'
  JSON = 'json'
  MPEG = 'mpeg'
  PLAIN = 'plain'
  STAR = '*'
  X_YAML = 'x-yaml'
  XML = 'xml'
  YAML = 'yaml'
minor_http_mime_types_by_name = {mime_type.value: mime_type for mime_type in MinorHTTPMIMETypes}

class HTTPMIMETypes(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, http_name, serializer_function_name, base_structure):
    name_tokens = http_name.split('/')
    self.major_type = major_http_mime_types_by_name[name_tokens[0]]
    self.minor_type = minor_http_mime_types_by_name[name_tokens[1]]
    
    self.serializer_function_name = serializer_function_name
    self.base_structure = base_structure
  
  def __eq__(self, other):
    return isinstance(other, HTTPMIMETypes) and \
      self.major_type == other.major_type and \
      self.minor_type == other.minor_type and \
      self.serializer_function_name == other.serializer_function_name and \
      self.base_structure == other.base_structure
  
  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __hash__(self):
    return ((((hash(self.major_type) * 397) ^ hash(self.minor_type) * 397) ^ hash(self.serializer_function_name)) * 397) ^ hash(self.base_structure)
  
  def __str__(self):
    return '%s/%s' % (self.major_type.value, self.minor_type.value)
  
  APPLICATION_JSON = 'application/json', 'to_json', '{"data": "%s"}'
  APPLICATION_X_YAML = 'application/x-yaml', 'to_yaml', 'data: %s'
  APPLICATION_XML = 'application/xml', 'to_xml', '<data>%s</data>'
  APPLICATION_YAML = 'application/yaml', 'to_yaml', 'data: %s'
  MEDIA_FLAC = 'audio/flac', None, bytes()
  MEDIA_MPEG = 'audio/mpeg', None, bytes()
  STAR_STAR = '*/*', None, bytes()
  TEXT_PLAIN = 'text/plain', None, '%s'

HTTPMIMETypes_by_name = {str(x): x for x in HTTPMIMETypes}
text_HTTPMIMETypes = \
{
  HTTPMIMETypes.APPLICATION_JSON,
  HTTPMIMETypes.APPLICATION_XML,
  HTTPMIMETypes.APPLICATION_X_YAML,
  HTTPMIMETypes.APPLICATION_YAML,
  HTTPMIMETypes.TEXT_PLAIN
}
default_text_HTTPMIMEType = HTTPMIMETypes.APPLICATION_JSON

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
def _parse_range_header(header: str) -> HTTPRange:
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
  
  def __hash__(self):
    return hash(self._header_name)
  
  def __eq__(self, other):
    return isinstance(other, type(self)) and \
      self._header_name == other._header_name
  
  def __ge__(self, other):
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name >= other._header_name
  
  def __gt__(self, other):
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name > other._header_name
  
  def __le__(self, other):
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name <= other._header_name
  
  def __lt__(self, other):
    if not isinstance(other, HTTPHeaders):
      raise TypeError('http headers can only be compared to other http headers.')
    
    return self._header_name < other._header_name
  
  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __str__(self):
    return self._header_name
  
  def get_value(self, environment:dict):
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
  
  def __hash__(self):
    return hash(self._code)
  
  def __eq__(self, other):
    return isinstance(other, HTTPStatusCodes) and \
      self._code == other._code
  
  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __str__(self):
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
  
  def __eq__(self, other):
    return isinstance(other, HTTPRequestMethods) and self._name == other._name
  
  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __hash__(self):
    return hash(self._name)
  
  def __str__(self):
    return self._name
  
  DELETE  = 'delete'
  GET     = 'get'
  OPTIONS = 'options'
  PATCH   = 'patch'
  POST    = 'post'
  PUT     = 'put'

HTTPRequestMethods_by_name = {rm.name.lower(): rm for rm in HTTPRequestMethods} | {rm.name.upper(): rm for rm in HTTPRequestMethods}

class Response:
  def __init__(self, payload, status_code:HTTPStatusCodes, mime_type:HTTPMIMETypes = None, serialization_falls_back_to_fields:bool = True, use_public_fields_only:bool = True, use_base_field_in_xml = False, use_base_field_in_yaml:bool = False, data_is_raw:bool = False, content_length:int = None, headers:dict[str, str] = None):
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
  
  def __str__(self):
    mime_was_none = False
    if self._mime_type is None:
      self._mime_type = HTTPMIMETypes.TEXT_PLAIN
      mime_was_none = True
    
    result = self.serialize()
    
    if mime_was_none:
      self._mime_type = None
    
    return result
  
  def get_status_code(self):
    return self._status_code
  
  def get_mime_type(self):
    return self._mime_type
  
  def set_mime_type(self, mime_type:HTTPMIMETypes):
    if not isinstance(mime_type, HTTPMIMETypes):
      raise TypeError('a mime type must be an HTTPMIMEType.')
    
    self._mime_type = mime_type
  
  def data_is_raw(self):
    return self._data_is_raw
  
  def get_headers(self):
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
  
  def get_content_length(self):
    return self._content_length
  
  def get_payload_as_bytes(self, encoding:str) -> bytes:
    if self._data_is_raw:
      return self.payload
    
    return bytes(self.serialize(), encoding)
  
  def serialize(self) -> str:
    if self._data_is_raw:
      return str(self.payload)
    
    if self.payload is None:
      return ''
    
    if self._mime_type is None:
      raise ValueError('no mime type was given.')
    
    serializer_function_name = self._mime_type.serializer_function_name
    
    if serializer_function_name is not None and hasattr(self.payload, serializer_function_name):
      serializer_function = getattr(self.payload, serializer_function_name)
      
      if callable(serializer_function) and len(signature(serializer_function).parameters) == 1:
        return serializer_function(self.payload)
    
    if self._fall_back_to_fields:
      return self.serialize_by_field()
    
    data = quote_plus(str(self.payload))
    return self._mime_type.base_structure % data
  
  def serialize_by_field(self):
    if self._data_is_raw:
      raise ValueError('raw data can\'t be serialized (by field or otherwise).')
    
    if self._mime_type is None:
      raise ValueError('no mime type was given.')
    
    if self._mime_type == HTTPMIMETypes.APPLICATION_JSON:
      return serialize_by_field_to_json(self.payload, self._use_public_fields_only)
    
    if self._mime_type == HTTPMIMETypes.APPLICATION_XML:
      return serialize_by_field_to_xml(self.payload, self._use_public_fields_only, self._use_base_field_in_xml)
    
    if self._mime_type == HTTPMIMETypes.APPLICATION_X_YAML or self._mime_type == HTTPMIMETypes.APPLICATION_YAML:
      return serialize_by_field_to_yaml(self.payload, self._use_public_fields_only, self._use_base_field_in_yaml)
    
    if self._mime_type == HTTPMIMETypes.TEXT_PLAIN:
      return serialize_by_field_to_plain_text(self.payload, self._use_public_fields_only)
    
    raise ValueError('can\'t serialize by field to %s.' % (self._mime_type, ))

class Message:
  def __init__(self, message:str):
    self.message = message
  
  def __eq__(self, other):
    if not isinstance(other, Message):
      return False
    
    return self.message == other.message
  
  def __ne__(self, other):
    if not isinstance(other, Message):
      return True
    
    return self.message != other.message
  
  def __hash__(self):
    return hash(self.message)
  
  def __add__(self, other):
    if isinstance(other, Message):
      return Message(self.message + other.message)
    elif isinstance(other, str):
      return Message(self.message + other)
    else:
      raise TypeError('can only add messages or strings to messages.')
  
  def __iadd__(self, other):
    if isinstance(other, Message):
      self.message += other.message
    elif isinstance(other, str):
      self.message += other
    else:
      raise TypeError('can only add messages or strings to messages.')
  
  def __str__(self):
    return self.message

circular_reference_text = quote_plus('<circular reference>')
_exclude_from_serialization = '_exclude_from_serialization'

def serialize_by_field_to_json(obj:any, public_only:bool = True, skip_null_values:bool = True, skip_circular_references:bool = True) -> str:
  result = _serialize_by_field_to_json(obj, public_only, skip_null_values, skip_circular_references)
  
  if result is None or len(result) == 0:
    result = '{}'
  
  return result

def _serialize_by_field_to_json(obj:any, public_only:bool, skip_null_values:bool, skip_circular_references:bool, seen_objs:list = None) -> str:
  if obj is None:
    if skip_null_values:
      return None
    
    return 'null'
  
  if isinstance(obj, Enum):
    obj = obj.value
  
  if isinstance(obj, bool):
    return 'true' if obj else 'false'
  
  if isinstance(obj, str):
    return '"%s"' % (quote_plus(obj), )
  
  if isinstance(obj, (list, set, tuple)):
    result = '['
    
    for item in obj:
      json_val = _serialize_by_field_to_json(item, public_only, skip_null_values, skip_circular_references, seen_objs)
      if json_val is None:
        continue
      
      if len(result) > 1:
        result += ', '
      
      result += json_val
    
    return result + ']'
  
  if isinstance(obj, dict):
    result = '{'
    
    for key in obj:
      json_val = _serialize_by_field_to_json(obj[key], public_only, skip_null_values, skip_circular_references, seen_objs)
      if json_val is None:
        continue
      
      if len(result) > 1:
        result += ', '
      
      result += '"%s": %s' % (quote_plus(str(key)), json_val)
    
    return result + '}'
  
  if is_primitive(obj):
    return quote_plus(str(obj))
  
  if seen_objs is None:
    seen_objs = list()
  
  if obj in seen_objs:
    if skip_circular_references:
      return None
    
    return '"%s"' % (circular_reference_text, )
  
  json_fields = []
  fields = obj.__dict__
  exclude_fields = fields.get(_exclude_from_serialization, set())
  for field_name in fields:
    if field_name == _exclude_from_serialization or field_name in exclude_fields:
      continue
    
    if skip_null_values and fields[field_name] is None:
      continue
    
    new_name = str(field_name)
    if new_name[0] == '_':
      if public_only:
        continue
      
      new_name = new_name[1:]
    
    if new_name is None:
      new_name = '<none>'
    else:
      new_name = quote_plus(new_name)
    
    serialized_value = _serialize_by_field_to_json(fields[field_name], public_only, skip_null_values, skip_circular_references, seen_objs + [obj])
    if serialized_value is None:
      serialized_value = '"%s"' % (circular_reference_text, )
    
    json_fields.append('"' + new_name + '": ' + serialized_value)
  
  return '{' + ', '.join(json_fields) + '}'

def serialize_by_field_to_xml(obj:any, public_only:bool = True, use_base_field:bool = False, skip_null_values:bool = True, skip_circular_references:bool = True) -> str:
  return _serialize_by_field_to_xml(obj, public_only, use_base_field, skip_null_values, skip_circular_references)

def _serialize_by_field_to_xml(obj:any, public_only:bool = True, use_base_field:bool = False, skip_null_values:bool = True, skip_circular_references:bool = True, seen_objs:list = None) -> str:
  if obj is None:
    if skip_null_values:
      return None
    
    return 'null'
  
  if isinstance(obj, Enum):
    obj = obj.value
  
  if isinstance(obj, (list, set, tuple)):
    result = ''
    
    for item in obj:
      xml_val = _serialize_by_field_to_xml(item, public_only, use_base_field, skip_null_values, skip_circular_references, seen_objs)
      if xml_val is None:
        continue
      
      result += '<item>%s</item>' % (xml_val, )
    
    return result
  
  if isinstance(obj, dict):
    result = ''
    
    for key in obj:
      xml_val = _serialize_by_field_to_xml(obj[key], public_only, use_base_field, skip_null_values, skip_circular_references, seen_objs)
      if xml_val is None:
        continue
      
      xml_key = quote_plus(str(key))
      result += '<%s>%s</%s>' % (xml_key, xml_val, xml_key)
    
    return result
  
  if is_primitive(obj):
    return quote_plus(str(obj))
  
  if seen_objs is None:
    seen_objs = list()
  
  if obj in seen_objs:
    if skip_circular_references:
      return None
    
    return circular_reference_text
  
  outter_tag = get_type_name(obj, True)
  result = ''
  if use_base_field:
    result = '<' + outter_tag + '>'
  
  fields = obj.__dict__
  exclude_fields = fields.get(_exclude_from_serialization, set())
  for field_name in fields:
    if field_name == _exclude_from_serialization or field_name in exclude_fields:
      continue
    
    if skip_null_values and fields[field_name] is None:
      continue
    
    new_name = str(field_name)
    if new_name[0] == '_':
      if public_only:
        continue
      
      new_name = new_name[1:]
    
    xml_val = _serialize_by_field_to_xml(fields[field_name], public_only, use_base_field, skip_null_values, skip_circular_references, seen_objs + [obj])
    if xml_val is None:
      continue
    
    new_name = quote_plus(new_name)
    result += '<%s>%s</%s>' % (new_name, xml_val, new_name)
  
  if use_base_field:
    result += '</' + outter_tag + '>'
  
  return result

yaml_indent = '  '
def serialize_by_field_to_yaml(obj:any, public_only:bool = True, use_base_field:bool = False, initial_indent:int = 0, skip_null_values:bool = True, skip_circular_references:bool = True) -> str:
  result = _serialize_by_field_to_yaml(obj, public_only, use_base_field, initial_indent, skip_null_values, skip_circular_references)
  
  if len(result) > 0 and result[0] == '\n':
    result = result[1:]
  
  return result

def _serialize_by_field_to_yaml(obj:any, public_only:bool, use_base_field:bool, indent:int, skip_null_values:bool, skip_circular_references:bool, seen_objs:list = None) -> str:
  result = ''
  if seen_objs is None:
    seen_objs = []
  
  if obj is None:
    if skip_null_values:
      return None
    return 'null'
  
  if isinstance(obj, str):
    return '"%s"' % (quote_plus(obj))
  
  if isinstance(obj, (list, set, tuple)):
    result = ''
    serd_start = '\n%s- ' % (yaml_indent * indent,)
    for item in obj:
      if skip_null_values and item is None:
        continue
      
      yaml_val = _serialize_by_field_to_yaml(item, public_only, use_base_field, indent + 1, skip_null_values, skip_circular_references, seen_objs)
      
      if yaml_val is None:
        continue
      
      while len(yaml_val) > 0 and yaml_val[0] == ' ':
        yaml_val = yaml_val[1:]
      
      result += serd_start + yaml_val
    return result
  
  if isinstance(obj, dict):
    result = ''
    for key in obj:
      if skip_null_values and obj[key] is None:
        continue
      
      yaml_val = _serialize_by_field_to_yaml(obj[key], public_only, use_base_field, indent + 1, skip_null_values, skip_circular_references, seen_objs)
      if yaml_val is None:
        continue
      
      yaml_key = quote_plus(str(key))
      result += '\n%s%s: %s' % (yaml_indent*indent, yaml_key, yaml_val)
    
    return result[1:]
  
  if is_primitive(obj):
    return quote_plus(str(obj))
  
  if obj in seen_objs:
    if skip_circular_references:
      return None
    else:
      return '"%s"' % (circular_reference_text, )
  
  if use_base_field:
    result += '\n%s%s:' % (yaml_indent*indent, get_type_name(obj, True))
    indent += 1
  
  fields = obj.__dict__
  exclude_fields = fields.get(_exclude_from_serialization, set())
  for field_name in fields:
    if field_name == _exclude_from_serialization or field_name in exclude_fields:
      continue
    
    if skip_null_values and fields[field_name] is None:
      continue
    
    raw_field_value = fields[field_name]
    if isinstance(raw_field_value, Enum):
      raw_field_value = raw_field_value.value
    
    field_value = _serialize_by_field_to_yaml(raw_field_value, public_only, use_base_field, indent + 1, skip_null_values, skip_circular_references, seen_objs + [obj])
    if field_value is None:
      continue
    elif len(field_value) > 0:
      if field_value == '"%s"' % (circular_reference_text, ) or (is_primitive(raw_field_value) and not isinstance(raw_field_value, (dict, list, set, tuple))):
        while field_value[0] == '\n':
          field_value = field_value[1:]
        field_value = ' ' + field_value
      elif field_value[0] != '\n':
        field_value = '\n%s' % (field_value, )
    
    new_name = str(field_name)
    if new_name[0] == '_':
      if public_only:
        continue
      
      new_name = new_name[1:]
    
    new_name = quote_plus(new_name)
    
    result += '\n%s%s:%s' % (yaml_indent*indent, new_name, field_value)
  
  while len(result) > 0 and result[0] == '\n':
    result = result[1:]
  
  return result

plain_text_indent = '  '
def serialize_by_field_to_plain_text(obj:any, public_only:bool = True, use_base_field:bool = True, indent:int = 0, skip_null_values:bool = True, skip_circular_references:bool = True) -> str:
  result = _serialize_by_field_to_plain_text(obj, public_only, use_base_field, indent, skip_null_values, skip_circular_references)
  
  if len(result) > 0 and result[0] == '\n':
    result = result[1:]
  
  return result

def _serialize_by_field_to_plain_text(obj:any, public_only:bool, use_base_field:bool, indent:int, skip_null_values:bool, skip_circular_references:bool, seen_objs:list = None) -> str:
  if obj is None:
    if skip_null_values:
      return None
    
    return 'null'
  
  if isinstance(obj, Enum):
    obj = obj.value
  
  if isinstance(obj, str):
    return '"' + quote_plus(str(obj)) + '"'
  
  last_indent = plain_text_indent*(indent - 1)
  this_indent = plain_text_indent*indent
  next_indent = plain_text_indent*(indent + 1)
  if isinstance(obj, (list, set, tuple)):
    if indent == 0:
      indent = 1
      last_indent = plain_text_indent * (indent - 1)
      this_indent = plain_text_indent * indent
      next_indent = plain_text_indent * (indent + 1)
    
    start = '['
    end   = ']'
    
    if isinstance(obj, set):
      start = '{'
      end   = '}'
    
    if isinstance(obj, tuple):
      start = '('
      end   = ')'
    
    result = '%s(%s)\n%s%s' % (last_indent, get_type_name(obj), last_indent, start)
    
    for item in obj:
      text_val = _serialize_by_field_to_plain_text(item, public_only, use_base_field, indent, skip_null_values, skip_circular_references, seen_objs)
      if text_val is None:
        continue
      
      while len(text_val) > 0 and text_val[0] in ('\n', ' '):
        text_val = text_val[1:]
      
      result += '\n%s%s,' % (this_indent, text_val)
    
    if len(obj) > 0:
      result = result[:-1]
    
    return '%s\n%s%s' % (result, last_indent, end)
  
  if isinstance(obj, dict):
    if indent == 0:
      indent = 1
      last_indent = plain_text_indent * (indent - 1)
      this_indent = plain_text_indent * indent
      next_indent = plain_text_indent * (indent + 1)
    
    result = '%s(dict)\n%s{' % (last_indent, last_indent)
    
    for key in obj:
      text_val = _serialize_by_field_to_plain_text(obj[key], public_only, use_base_field, indent + 1, skip_null_values, skip_circular_references, seen_objs)
      if text_val is None:
        continue
      
      first_idx = 0
      while text_val[first_idx] == '\n' or text_val[first_idx] == ' ':
        first_idx += 1
      text_val = text_val[first_idx:]
      
      text_key = str(key)
      if isinstance(key, str):
        text_key = '"%s"' % text_key
      
      result += '\n%s%s: %s,' % (this_indent, text_key, text_val)
    
    if len(obj) > 0:
      result = result[:-1]
    
    return '%s\n%s%s' % (result, last_indent, '}')
  
  if is_primitive(obj):
    return quote_plus(str(obj))
  
  if seen_objs is None:
    seen_objs = list()
  
  if obj in seen_objs:
    if skip_circular_references:
      return None
    
    return circular_reference_text
  
  result = ''
  field_indent = this_indent
  if use_base_field:
    result += '\n%s%s:' % (this_indent, get_type_name(obj, True))
    indent += 1
    field_indent = next_indent
  
  fields = obj.__dict__
  for field_name in fields:
    if skip_null_values and fields[field_name] is None:
      continue
    
    new_name = str(field_name)
    if new_name[0] == '_':
      if public_only:
        continue
      
      new_name = new_name[1:]
    
    text_val = _serialize_by_field_to_plain_text(fields[field_name], public_only, use_base_field, indent + 1, skip_null_values, skip_circular_references, seen_objs + [obj])
    if text_val is None:
      continue
    
    if len(text_val) > 0 and text_val[0] != '\n':
      first_idx = 0
      while text_val[first_idx] == ' ':
        first_idx += 1
      text_val = text_val[first_idx:]
      
      text_val = ' %s' % (text_val, )
    
    new_name = quote_plus(new_name)
    result += '\n%s%s:%s' % (field_indent, new_name, text_val)
  
  return result

class ResponseMessage:
  def __init__(self, message:str):
    if not isinstance(message, str):
      raise TypeError('give me a string for an error message, nub.')
    
    self.message = message
  
  def __str__(self):
    return str(self.message)

def build_http_response_from_exception(exception:Exception, mime_type:HTTPMIMETypes = None):
  grievances = []
  
  if not isinstance(exception, Exception):
    grievances.append('an exception must be an Exception.')
  
  if mime_type is not None and not isinstance(mime_type, HTTPMIMETypes):
    grievances.append('a mime_type must be an HTTPMIMEType.')
  
  if len(grievances) > 0:
    raise TypeError('\n'.join(grievances))
  
  if not isinstance(exception, BaseHTTPException):
    log_exception(exception)
    return Response(ResponseMessage("an internal error occurred."), HTTPStatusCodes.HTTP500, mime_type)
  
  return Response(ResponseMessage(exception.get_message()), HTTPStatusCodes_by_code[exception.get_status()], mime_type)

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
    return get_param(self.param_name, params, self._parse_func, self._exception_param_type_name, self.is_required, 'query',
                     self.default_value, return_error_message)

class PathParam(Enum):
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
    return self.param_name + ' (' + self.type_name + ')'
  
  def get_value(self, path_params:dict[str, str], return_error_message = True):
    return get_param(self.param_name, path_params, self._parse_func, self._param_type_name_for_exceptions, True, 'path', None, return_error_message)

def get_param(key:str, params:dict, parser, type_name:str, required:bool = False, param_type:str = 'query', default_value=None, return_error_message:bool = False):
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