def get_nth_fibonacci_number(n:int) -> int:
  if n == 1 or n == 2:
    return 1
  
  # this case maintains the property that the nth fibonacci number + the (n+1)th fibonnacci number = the (n+2)th fibonacci ... but it works for n <= 0.
  if n < 1:
    a, b, i = 1, 1, 0
    
    while i >= n:
      a, b, i = b, a - b, i - 1
    
    return b
  
  a, b = 1, 1
  
  for i in range(n - 2):
    a, b = b, a + b
  
  return b