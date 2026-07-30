from exceptions.http_base import BaseHTTPException
from models.http import HTTPMIMETypes, Response, Message, HTTPStatusCodes, HTTPStatusCodes_by_code
from util.infrastructure.logger import log_exception

def build_http_response_from_exception(exception:Exception, mime_type:HTTPMIMETypes = None):
  grievances = []
  
  if not isinstance(exception, Exception):
    grievances.append('an exception must be an Exception.')
  
  if mime_type is not None and not isinstance(mime_type, HTTPMIMETypes):
    grievances.append('a mime_type must be an HTTPMIMEType.')
  
  if len(grievances) > 0:
    raise TypeError('\n'.join(grievances))
  
  if not isinstance(exception, BaseHTTPException):
    log_exception(exception)
    return Response(Message("an internal error occurred."), HTTPStatusCodes.HTTP500, mime_type)
  
  return Response(Message(exception.get_message()), HTTPStatusCodes_by_code[exception.get_status()], mime_type)
