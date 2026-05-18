from exceptions.http_base import BadRequestException
from logic.fibonacci import get_nth_fibonacci_number
from util.http import Response, HTTPStatusCodes
from models.http import AvailablePath, HTTPMIMETypes, EndpointData
from util.interface.fibonacci import FibonacciPathParams

class Result:
  def __init__(self, result:int):
    self.result = result

def _get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  n, n_error = FibonacciPathParams.N.get_value(path_params, True)
  if n_error is not None:
    raise BadRequestException(n_error)
  
  fibb = get_nth_fibonacci_number(n)
  
  return Response(Result(fibb), HTTPStatusCodes.HTTP200)

get = EndpointData \
(
  _get,
  AvailablePath(description='this endpoint calculates and returns the nth fibonacci number.'),
  { HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML },
  HTTPMIMETypes.APPLICATION_YAML
)