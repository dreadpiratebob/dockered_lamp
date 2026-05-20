# yes, the capitalization in this class name will make some people angry.  no, i don't care.
class MySQLMessage:
  def __init__(self, id:int, content:str):
    grievances = []
    
    if id is not None and not isinstance(id, int):
      grievances.append('a message id must be an integer.')
    
    if content is not None and not isinstance(content, str):
      grievances.append('message content must be an string.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    self._id = id
    self._content = content
  
  def __eq__(self, other) -> bool:
    return isinstance(other, MySQLMessage) and \
      self._id == other._id and \
      self._content == other._content
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
  
  def __repr__(self) -> str:
    return 'MySQLMessage(' + repr(self._id) + ', ' + repr(self._content) + ')'
  
  def __str__(self) -> str:
    return self._content
  
  def __add__(self, other) -> 'MySQLMessage':
    if isinstance(other, MySQLMessage):
      return MySQLMessage(None, self._content + other._content)
    
    if isinstance(other, str):
      return MySQLMessage(None, self._content + other)
    
    raise TypeError('only a MySQLMessage or a string can be added to a MySQLMessage.')