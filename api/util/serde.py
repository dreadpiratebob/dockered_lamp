from api.exceptions.http_base import BadRequestException
from api.util.http import HTTPMIMETypes

from json import loads as parse_json
from json.decoder import JSONDecodeError

from xmltodict import parse as parse_xml
from xml.parsers.expat import ExpatError as XMLDecoderError

from yaml import load as parse_yaml, SafeLoader, FullLoader
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