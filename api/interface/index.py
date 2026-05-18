from util.http import HTTPRequestMethods, HTTPStatusCodes, Response
from models.http import HTTPMIMETypes, EndpointData


class AvailablePaths:
  def __init__(self, paths:set):
    self.paths = paths
  
  def __str__(self):
    return str(self.paths)

def _get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  paths = set()
  
  start_path = '/interface'
  nodes_to_process = [environment['root_path_node']]
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
      
      paths.add(path_help)
    
    for child in current_node.get_children():
      nodes_to_process.append(child)
  
  return Response(AvailablePaths(paths), HTTPStatusCodes.HTTP200)

get = EndpointData \
(
  _get,
  None,
  { HTTPMIMETypes.APPLICATION_JSON, HTTPMIMETypes.APPLICATION_XML, HTTPMIMETypes.APPLICATION_X_YAML, HTTPMIMETypes.APPLICATION_YAML },
  HTTPMIMETypes.APPLICATION_YAML,
)