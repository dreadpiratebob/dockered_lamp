import math

def int_to_str(value: int) -> str:
  if not isinstance(value, int):
    raise TypeError('this only converts integers to strings.')
  
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

def serialize(obj:any) -> str:
  if isinstance(obj, str):
    return obj
  
  if isinstance(obj, bool):
    return 'true' if obj else 'false'
  
  if isinstance(obj, int):
    return int_to_str(obj)
  
  raise TypeError('this only converts string, booleans and integers to strings.')
