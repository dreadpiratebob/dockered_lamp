from models.http import PathParams

class FibonacciPathParams(PathParams):
  N = 'n', 'integer', 'an integer', 'the index of the number in the fibonacci sequence to get', int