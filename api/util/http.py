from models.http import HTTPMIMETypes, Response
from util.functions import get_type_name, is_primitive

from enum import Enum
from inspect import signature
from urllib.parse import quote_plus

text_HTTPMIMETypes = \
{
  HTTPMIMETypes.APPLICATION_JSON,
  HTTPMIMETypes.APPLICATION_XML,
  HTTPMIMETypes.APPLICATION_X_YAML,
  HTTPMIMETypes.APPLICATION_YAML,
  HTTPMIMETypes.TEXT_PLAIN
}
default_text_HTTPMIMEType = HTTPMIMETypes.APPLICATION_JSON

def get_response_payload_as_bytes(response:Response, encoding:str, fail_on_missing_mime_type:bool = True) -> bytes:
  if response.data_is_raw():
    return response.payload
  
  return bytes(serialize_response(response, fail_on_missing_mime_type), encoding)

def serialize_response(response:Response, fail_on_missing_mime_type:bool = True) -> str:
  if response.data_is_raw():
    return str(response.payload)
  
  if response.payload is None:
    return ''
  
  mime_type_was_none = False
  result = None
  if response.get_mime_type() is None:
    if fail_on_missing_mime_type:
      raise ValueError('no mime type was given.')
    else:
      response.set_mime_type(HTTPMIMETypes.TEXT_PLAIN)
      mime_type_was_none = True
  
  serializer_function_name = response.get_mime_type().serializer_function_name
  if serializer_function_name is not None and hasattr(response.payload, serializer_function_name):
    serializer_function = getattr(response.payload, serializer_function_name)
    
    if callable(serializer_function) and len(signature(serializer_function).parameters) == 1:
      result = serializer_function(response.payload)
  elif response.serialization_falls_back_to_fields():
    result = serialize_response_by_field(response)
  else:
    data = quote_plus(str(response.payload))
    result = response.get_mime_type().base_structure % (data, )
  
  if mime_type_was_none:
    response.set_mime_type(None)
  
  return result

# there's probly a better way to do this.  i kinda want generics.
_response_serializers_by_mime_type = \
{
  HTTPMIMETypes.APPLICATION_JSON:lambda response:serialize_by_field_to_json(response.payload, response.use_public_fields_only()),
  HTTPMIMETypes.TEXT_PLAIN:lambda response:serialize_by_field_to_plain_text(response.payload, response.use_public_fields_only()),
  HTTPMIMETypes.APPLICATION_XML:lambda response:serialize_by_field_to_xml(response.payload, response.use_public_fields_only(), response.use_base_field_in_xml()),
  HTTPMIMETypes.APPLICATION_X_YAML:lambda response:serialize_by_field_to_yaml(response.payload, response.use_public_fields_only(), response.use_base_field_in_yaml()),
  HTTPMIMETypes.APPLICATION_YAML:lambda response:serialize_by_field_to_yaml(response.payload, response.use_public_fields_only(), response.use_base_field_in_yaml()),
}
def serialize_response_by_field(response:Response) -> str:
  if response.data_is_raw():
    raise ValueError('raw data can\'t be serialized (by field or otherwise).')
  
  if response.get_mime_type() not in _response_serializers_by_mime_type:
    raise ValueError('can\'t serialize by field to %s.' % (response.get_mime_type(), ))
  
  return _response_serializers_by_mime_type[response.get_mime_type()](response)

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

def set_response_properties() -> None:
  # monkey patching to avoid circular references, so that i can put models in one file and serde functions in a different file.
  
  def _repr(self: Response) -> str:
    result = serialize_response(self, False)
    
    if self.get_mime_type() is None:
      return result
    
    return '%s (%s)' % (result, self.get_mime_type())
  
  Response.__repr__ = _repr
  
  def _str(self: Response) -> str:
    return serialize_response(self, False)
  
  Response.__str__ = _str
set_response_properties()