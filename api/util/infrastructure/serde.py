from exceptions.http_base import BadRequestException
from models.http import HTTPMIMETypes

import math

from json import loads as parse_json
from json.decoder import JSONDecodeError

from xmltodict import parse as parse_xml
from xml.parsers.expat import ExpatError as XMLDecoderError

from yaml import load as parse_yaml, FullLoader
from yaml.scanner import ScannerError as YAMLDecoderError

_raw_text_error = 'text to deserialize must be a string.'
_decode_error = 'couldn\'t parse the %s "%s".  (%s)'
def get_dict(raw_text:str, content_type:HTTPMIMETypes) -> dict[str, str]:
  if not isinstance(raw_text, str):
    raise TypeError(_raw_text_error)
  
  try:
    if content_type == HTTPMIMETypes.APPLICATION_JSON:
      return parse_json(raw_text)
    
    if content_type == HTTPMIMETypes.APPLICATION_XML:
      return parse_xml(raw_text)
    
    if content_type == HTTPMIMETypes.APPLICATION_YAML or content_type == HTTPMIMETypes.APPLICATION_X_YAML:
      return parse_yaml(raw_text, Loader=FullLoader)
    
  except JSONDecodeError as e:
    raise BadRequestException(_decode_error % ('JSON', raw_text, e.msg))
  except XMLDecoderError as e:
    raise BadRequestException(_decode_error % ('XML',  raw_text, str(e)))
  except YAMLDecoderError as e:
    raise BadRequestException(_decode_error % ('YAML', raw_text, str(e)))
  
  raise ValueError('unknown MIME type "%s".' % (content_type.name,))

def int_to_str(value:int) -> str:
  if not isinstance(value, int):
    raise TypeError('this only converts integers to strings.')
  
  print('value: %s' % (value, ))
  if math.log(value, 10) < 4300:
    return str(value)
  
  result = []
  i = value
  while i > 0:
    result.insert(0, str(i % 10))
    i = i // 10
  
  if value < 0:
    result.insert(0, '-')
  
  return ''.join(result)