from util.http import PathParam

class FibonacciPathParams(PathParam):
  N = 'n', 'integer', 'an integer', 'the index of the number in the fibonacci sequence to get', int