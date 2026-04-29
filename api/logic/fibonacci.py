from exceptions.http_base import BadRequestException

def get_nth_fibonacci_number(n:int) -> int:
  if n <= 0:
    raise BadRequestException('an index in the Fibonacci sequence must be positive.')
  
  if n <= 2:
    return 1
  
  a, b = 1, 1
  for i in range(n - 2):
    a, b = b, a + b
  
  return b