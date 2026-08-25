from models.environment import EnvironmentKeys
from models.http import EndpointData, HTTPMIMETypes, HTTPRequestMethods, HTTPStatusCodes, Response

class AvailableEndpoints:
  def __init__(self, endpoints:set):
    self.endpoints = endpoints
  
  def __str__(self):
    return str(self.paths)

def _get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  endpoints = set()
  
  start_path = '/interface'
  nodes_to_process = []
  if EnvironmentKeys.ROOT_PATH_NODE in environment:
    nodes_to_process.append(environment[EnvironmentKeys.ROOT_PATH_NODE])
  
  while len(nodes_to_process) > 0:
    current_node = nodes_to_process.pop(0)
    
    for request_method in HTTPRequestMethods:
      if current_node.get_request_method_func(request_method) is None:
        continue
      
      path_help = current_node.get_request_method_help(request_method)
      
      if path_help is None:
        continue
      
      if path_help.request_method is None:
        path_help.request_method = str(request_method).upper()
      
      if path_help.path is None:
        path_help.path = current_node.get_pretty_path()[len(start_path):]
      
      endpoints.add(path_help)
    
    for child in current_node.get_children():
      nodes_to_process.append(child)
  
  return Response(AvailableEndpoints(endpoints), HTTPStatusCodes.HTTP200)

get = EndpointData \
(
  _get,
  None,
  { HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML },
  HTTPMIMETypes.APPLICATION_YAML
)