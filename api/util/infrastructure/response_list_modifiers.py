from util.infrastructure.functions import get_search_text_from_raw_text, get_type_name

from enum import Enum

class FilterInfo:
  def __init__(self, id:int, name:str, has_wildcards:bool, is_case_sensitive:bool, matches_diacritics:bool, filter_on_null:bool):
    grievances = []
    
    if id is not None and not isinstance(id, int):
      grievances.append('an id must be an int.')
    
    lcase_name, diacriticless_name, lcase_no_diacritic_name = (name, name, name)
    if name is not None:
      if isinstance(name, str):
        lcase_name, diacriticless_name, lcase_no_diacritic_name = get_search_text_from_raw_text(name)
      else:
        grievances.append('a name must be a string.')
    
    if not isinstance(has_wildcards, bool):
      grievances.append('the "has wildcards" flag must be a boolean.')
    
    if not isinstance(is_case_sensitive, bool):
      grievances.append('the "is case sensitive" flag must be a boolean.')
    
    if not isinstance(matches_diacritics, bool):
      grievances.append('the "matches diacritics" flag must be a boolean.')
    
    if not isinstance(filter_on_null, bool):
      grievances.append('the "filter on null" flag must be a boolean.')
    
    if not is_case_sensitive and not matches_diacritics:
      name = lcase_no_diacritic_name
    elif not is_case_sensitive:
      name = lcase_name
    elif not matches_diacritics:
      name = diacriticless_name
    
    self.id = id
    self.name = name
    self.name_has_wildcards = has_wildcards
    self.name_is_case_sensitive = is_case_sensitive
    self.name_matches_diacritics = matches_diacritics
    self.filter_on_null = filter_on_null
  
  def __eq__(self, other) -> bool:
    if not isinstance(other, type(self)):
      return False
    
    for field_name in self.__dict__:
      if self.__dict__[field_name] != other.__dict__[field_name]:
        return False
    
    return True
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    result = 0
    
    for field_name in self.__dict__:
      result = (result * 397) * hash(self.__dict__[field_name])
    
    return result
  
  def __str__(self) -> str:
    return 'filter info: { %s }' % (', '.join(['%s: %s' % (field, self.__dict__[field]) for field in self.__dict__]),)
  
  def clone(self):
    return FilterInfo(self.id, self.name, self.name_has_wildcards, self.name_is_case_sensitive, self.name_matches_diacritics, self.filter_on_null)
  
  def get_search_adjusted_name(self) -> str:
    if self.name_is_case_sensitive and self.name_matches_diacritics:
      return self.name
    
    lcase_name, no_diacritic_name, lcase_no_diacritic_name = get_search_text_from_raw_text(self.name)
    
    if not self.name_is_case_sensitive and self.name_matches_diacritics:
      return lcase_name
    
    if self.name_is_case_sensitive and not self.name_matches_diacritics:
      return no_diacritic_name
    
    return lcase_no_diacritic_name

default_filter_info = FilterInfo(None, None, False, True, True, False)

class OrderColName(Enum):
  def __new__(self, *args, **kwds):
    value = len(self.__members__) + 1
    obj = object.__new__(self)
    obj._value_ = value
    return obj
  
  def __init__(self, query_name:str, table_name:str, column_name:str, description:str):
    self.query_name = query_name
    self.table_name = table_name
    self.column_name = column_name
    self.description = description

class OrderDirection(Enum):
  ASCENDING = 'ASC'
  DESCENDING = 'DESC'

def get_order_direction(input:str) -> OrderDirection:
  input = input.lower()
  
  if input in (OrderDirection.ASCENDING.value.lower(), 'ascending'):
    return OrderDirection.ASCENDING
  
  if input in (OrderDirection.DESCENDING.value.lower(), 'descending'):
    return OrderDirection.DESCENDING
  
  raise ValueError('the value "%s" can\'t be parsed as an order direction.' % (str(input), ))

class OrderByCol:
  def __init__(self, col:OrderColName, direction:OrderDirection):
    self.col = col
    self.direction = direction
  
  def __eq__(self, other):
    return isinstance(other, OrderByCol) and \
      self.col == other.col and \
      self.direction == other.direction
  
  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __hash__(self):
    return (hash(self.col) * 397) ^ hash(self.direction)
  
  def __str__(self):
    return '%s %s' % (self.col.column_name, self.direction.value)

class OrderParser:
  def __init__(self, cols:type(OrderColName), cols_by_name=None):
    self._cols = cols
    
    if cols_by_name is None:
      self._cols_by_name = {col.query_name: col for col in cols}
    elif isinstance(cols_by_name, dict):
      self._cols_by_name = cols_by_name
    else:
      raise TypeError('cols_by_name must be None or a dict')
  
  def parse(self, input:str) -> list[OrderByCol]:
    result = []
    tokens = input.split(',')
    if len(tokens) <= 0:
      raise ValueError('no column names were found.')
    
    for token in tokens:
      token = token.strip(' \t')
      
      pieces = token.split(' ')
      if len(pieces) > 2:
        raise ValueError('the order piece "%s" has too many spaces; a column name can\'t have spaces, so each piece should have at most one space.' % (token, ))
      
      if pieces[0] not in self._cols_by_name:
        raise ValueError('"%s" isn\'t a valid column name; valid column names are %s.' % (pieces[0], ', '.join([col.column_name for col in self._cols]),))
      
      _col = self._cols_by_name[pieces[0]]
      _dir = OrderDirection.ASCENDING
      if len(pieces) == 2:
        _dir = get_order_direction(pieces[1])
      
      result.append(OrderByCol(_col, _dir))
    
    return result

def get_order_clause(order_bys:[list[OrderByCol], tuple[OrderByCol]]) -> str:
  if len(order_bys) == 0:
    return ''
  
  return 'ORDER BY %s' % ('\n'.join(['%s%s %s' % ('' if ob.col.table_name is None else (ob.col.table_name + '.'), ob.col.column_name, ob.direction.value) for ob in order_bys]), )

def is_valid_order_by(order_by:any, subclass:type) -> bool:
  if order_by is None:
    return True
  
  if not isinstance(order_by, (list, tuple)):
    return False
  
  found_cols = set()
  for ob in order_by:
    if not isinstance(ob, OrderByCol) or not isinstance(ob.col, subclass):
      return False
    
    if ob.col in found_cols:
      return False
    
    found_cols.add(ob.col)
  
  return True

class PageInfo:
  def __init__(self, page_number:int, page_size:int):
    grievances = []
    
    if not isinstance(page_number, int):
      grievances.append('a page number must be an integer.')
    
    if page_size is not None and not isinstance(page_size, int):
      grievances.append('a page size must be None or an integer.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    if page_number < 1:
      grievances.append('a page number must be at least 1.')
    
    if page_size is not None and page_size < 1:
      grievances.append('a page size must be at least 1.')
    
    if len(grievances) > 0:
      raise ValueError('\n'.join(grievances))
    
    self.page_number = 1 if page_size is None else page_number
    self.page_size = page_size
  
  def __eq__(self, other:any) -> bool:
    if not isinstance(other, type(self)):
      return False
    
    for field_name in self.__dict__:
      if self.__dict__[field_name] != other.__dict__[field_name]:
        return False
    
    return True
  
  def __ne__(self, other:any) -> bool:
    return not self.__eq__(other)
  
  def __hash__(self) -> int:
    result = 0
    
    for field_name in self.__dict__:
      result = result * 397 ^ hash(self.__dict__[field_name])
    
    return result
  
  def __repr__(self) -> str:
    return 'page #%s with %s items' % (self.page_number, self.page_size)
  
  def __str__(self) -> str:
    if self.page_size is None:
      return ''
    
    return 'LIMIT %s OFFSET %s' % (self.page_size, (self.page_number - 1) * self.page_size)
default_page_info = PageInfo(1, None)

def is_valid_page_info(obj:any) -> bool:
  if obj is None:
    return True
  
  if not isinstance(obj, PageInfo):
    return False
  
  if not isinstance(obj.page_number, int):
    return False
  
  if obj.page_size is not None and not isinstance(obj.page_size, int):
    return False
  
  if obj.page_number != 1 and obj.page_size is None:
    return False
  
  return True

def parse_page_size(input:str) -> int:
  input = input.lower()
  
  if input == 'all':
    return None
  
  return int(input)