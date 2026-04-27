class BaseHTTPException(Exception):
  def __init__(self, message:str, status:int):
    grievances = []
    
    if not isinstance(message, str):
      grievances.append('an error message must be a str.')
    
    if not isinstance(status, int):
      grievances.append('an http status must be an int.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    super().__init__(message)
    
    self._message = message
    self._status = status
  
  def get_message(self):
    return self._message
  
  def get_status(self):
    return self._status

# 400
class BadRequestException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 400)

# 401
class UnauthorizedException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 401)

# 403
class UnauthenticatedException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 403)

# 404
class NotFoundException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 404)

# 405
allowed_methods = {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}
invalid_http_method_error_message = 'an http method must be one of ' + str(allowed_methods)[1:-1] + ', but %s was given.'
class MethodNotAllowedException(BaseHTTPException):
  def __init__(self, method:str, endpoint:str):
    if not isinstance(method, str):
      raise TypeError(invalid_http_method_error_message % ('a ' + str(type(method))[8:-2], ))
    
    method = method.lower()
    if method not in allowed_methods:
      raise ValueError(invalid_http_method_error_message % ('%s (a %s)' % (method, str(type(method))[8:-2])))
    
    if not isinstance(endpoint, str):
      raise TypeError('an endpoint must be a string.')
    
    super().__init__('the request method "%s" isn\'t allowed for the endpoint %s.' % (method, endpoint), 405)

# 416
class RangeNotSatisfiableException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 416)

# 418
class ImATeapotException(BaseHTTPException):
  def __init__(self, message:str):
    super().__init__(message, 418)

# 500
class InternalServerError(Exception):
  def __init__(self, message):
    super().__init__(message)

#501
class NotImplementedException(BaseHTTPException):
  def __init__(self, message):
    super().__init__(message, 501)

class AmbiguousPathException(Exception):
  def __init__(self, paths):
    super().__init__('these paths are ambiguous:\n' + '\n'.join(paths))

class AuthorizationNotFoundException(UnauthenticatedException):
  def __init__(self):
    super().__init__('the Bearer token provided in the Authorization header doesn\'t exist or is invalid.')
