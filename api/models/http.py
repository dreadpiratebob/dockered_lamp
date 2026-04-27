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
    
    for range in self.ranges:
      if not isinstance(range[1], int):
        return None
      
      if not isinstance(range[0], int):
        result += range[1]
        continue
      
      result += range[1] - range[0]
  
  def __str__(self) -> str:
    result = '%s=' % self.unit
    
    for range in self.ranges:
      result += '%s-%s' % (range[0], range[1])
    
    return result