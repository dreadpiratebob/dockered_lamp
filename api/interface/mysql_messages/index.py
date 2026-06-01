from exceptions.http_base import BadRequestException
from logic.mysql_messages import get_mysql_messages, save_message
from models.db import MySQLMessage
from models.http import AvailablePath, EndpointData, HTTPMIMETypes, HTTPStatusCodes, Response
from util.service.mysql_messages import MySQLMessageQueryParams

class Messages:
  def __init__(self, messages:list[MySQLMessage]):
    self.messages = messages

def _get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  content_filter, content_filter_error = MySQLMessageQueryParams.CONTENT_FILTER.get_value(query_params)
  if content_filter_error is not None:
    raise BadRequestException(content_filter_error)
  
  messages = get_mysql_messages(content_filter)
  
  status_code = HTTPStatusCodes.HTTP200
  if len(messages) == 0:
    status_code = HTTPStatusCodes.HTTP204
  
  response_body = Messages(messages)
  
  return Response(response_body, status_code, use_public_fields_only=False)

get = EndpointData \
(
  _get,
  AvailablePath(query_params = (MySQLMessageQueryParams.CONTENT_FILTER, ), description = ''),
  {HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML},
  HTTPMIMETypes.APPLICATION_YAML
)

def _post(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  message_content = ''
  for c in body:
    message_content += chr(c)
  
  mysql_message = MySQLMessage(None, message_content)
  
  result = save_message(mysql_message)
  status_code = HTTPStatusCodes.HTTP200
  
  return Response(result, status_code, use_public_fields_only=False)

post = EndpointData \
(
  _post,
  AvailablePath(expected_body='the raw contents of the message to save.', description = 'this stores the request body as a message, gives it an id and then returns both the id and contents in the response body.'),
  {HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML},
  HTTPMIMETypes.APPLICATION_YAML
)