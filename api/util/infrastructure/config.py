from util.infrastructure.functions import get_type_name
from util.infrastructure.logger import get_logger

from os import path

def _get_base_api_path() -> str:
  base_path = path.dirname(__file__).replace('\\', '/')
  
  if len(base_path) > 0 and base_path.rfind('/') > -1:
    base_path = base_path[:base_path.rfind('/')]
  
  if len(base_path) > 0 and base_path.rfind('/') > -1:
    base_path = base_path[:base_path.rfind('/')]
  
  return base_path
base_api_path = _get_base_api_path()

_config = dict()

config_file_extension = '.conf'
key_val_assignment = ' = '
def load_config(config_name:str = 'main'):
  if not isinstance(config_name, str):
    raise TypeError('a config name must be a string.  (found a %s instead: "%s")' % (get_type_name(config_name), str(config_name)))
  
  full_filename = '%s/config/%s%s' % (base_api_path, config_name, config_file_extension)
  if not path.exists(full_filename):
    raise ValueError('no config called "%s" exists.  (looking in "%s".)' % (config_name, full_filename))
  
  global _config
  _config = dict()
  
  raw_content = None
  with open(full_filename, 'r') as config_file:
    raw_content = config_file.readlines()
  
  line_number = 0
  for config_line in raw_content:
    line_number += 1
    
    while len(config_line) > 0 and (config_line[-1] == '\r' or config_line[-1] == '\n'):
      config_line = config_line[:-1]
    
    if len(config_line) == 0 or config_line[0] == '#':
      continue
    
    chunks = config_line.split(key_val_assignment)
    if len(chunks) < 2:
      get_logger().error('line number %s in the config %s%s is invalid.  (found "%s", which is not in the format "key = value".)' % (str(line_number), config_name, config_file_extension, config_line))
      continue
    
    key = chunks[0]
    value = key_val_assignment.join(chunks[1:])
    
    if len(value) > 1 and ((value[0] == '\'' and value[-1] == '\'') or (value[0] == '\"' and value[-1] == '\"')):
      value = value[1:-1]
    
    _config[key] = value

def config_key_exists(key:str) -> bool:
  return key in _config

def get_config_value(key:str, default_value = None) -> any:
  return _config.get(key, default_value)

def set_config_value(key:str, value:any):
  _config[key] = value

load_config()