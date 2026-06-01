from models.http import AvailablePath, HTTPMIMETypes, EndpointData, HTTPStatusCodes, Message, Response

def _get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  return Response(Message('hello.'), HTTPStatusCodes.HTTP200)

get = EndpointData \
(
  _get,
  AvailablePath(description='this allows an HTTP client to get a message and ensure that requests work.'),
  { HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML },
  HTTPMIMETypes.APPLICATION_YAML
)