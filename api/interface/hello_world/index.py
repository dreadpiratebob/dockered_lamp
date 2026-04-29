from util.http import HTTPStatusCodes, HTTPMIMETypes, Message, Response
from util.http_path import AvailablePath

def get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  return Response(Message('hello.'), HTTPStatusCodes.HTTP200)

get_help = AvailablePath(description='this allows an HTTP client to get a message and ensure that requests work.')
get_allowed_accept_types = { HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML }
get_default_content_type = HTTPMIMETypes.APPLICATION_YAML