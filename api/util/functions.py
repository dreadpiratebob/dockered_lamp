from enum import Enum
from unidecode import unidecode

_char_replacements = \
{
  '​': '',
  '☾': '_',
  '☽': '_',
  '♡': 'heart',
  '⛧': 'star',
  '☆': 'star',
  '★': 'star',
  '⁰': '0',
  '¹': '1',
  '²': '2',
  '³': '3',
  '３': '3',
  '⁵': '5',
  '｡': '_',
  '◕': '_',
  '‿': '_',
  '&': 'and',
  '∆': 'D',
  '第': 'dai',
  'ヘ': 'he',
  '変': 'hen',
  '京': 'kyo',
  'メ': 'me',
  'ン': 'n',
  'ラ': 'ra',
  '市': 'shi',
  '新': 'shin',
  '態': 'tai',
  '東': 'to',
}
_diacritic_removal_special_cases = \
{
  '': ''
}
def get_search_text_from_raw_text(input_text:str) -> tuple[str, str, str]:
  raw_text = '' + input_text
  lcase = raw_text.lower()
  
  if raw_text in _diacritic_removal_special_cases:
    no_diacritics = _diacritic_removal_special_cases[raw_text]
  else:
    raw_text = ''
    for char in input_text:
      if char in _char_replacements:
        raw_text += _char_replacements[char]
      else:
        raw_text += char
    
    no_diacritics = unidecode(raw_text)
  
  lcase_no_diacritics = no_diacritics.lower()
  
  return lcase, no_diacritics, lcase_no_diacritics

def get_type_name(value:any, class_only:bool = False) -> str:
  start_index = 8
  if isinstance(value, Enum):
    start_index = 7
  
  result = str(type(value))[start_index:-2]
  
  if not class_only:
    return result
  
  return result[result.rfind('.') + 1:]

def hash_dict(d:dict) -> int:
  result = 0
  
  sorted_keys = [key for key in d]
  sorted_keys.sort()
  for key in sorted_keys:
    result = (((result * 397) ^ hash(key)) * 397) ^ hash(d[key])
  
  return result

def hash_list_or_tuple(obj:[list, tuple]) -> int:
  if not isinstance(obj, (list, tuple)):
    raise TypeError('to hash a list or tuple, you have to start with a list or tuple.')
  
  result = 0
  
  for item in obj:
    new_hash = 0
    if isinstance(item, (list, tuple)):
      new_hash = hash_list_or_tuple(item)
    elif isinstance(item, dict):
      new_hash = hash_dict(item)
    else:
      new_hash = hash(item)
    
    result = result * 397 ^ new_hash
  
  return result

def is_primitive(obj:any) -> bool:
  return not hasattr(obj, '__dict__')