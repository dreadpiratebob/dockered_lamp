from api.util.http import HTTPRequestMethods, HTTPStatusCodes, Response
from api.util.http_path import path_tries

class AvailablePath:
  def __init__(self, request_method:str, path:str, additional_information:str = ''):
    self.request_method = request_method.upper()
    self.path = path
    self.additional_information = additional_information
  
  def __eq__(self, other):
    return isinstance(other, AvailablePath) and \
      self.request_method == other.request_method and \
      self.path == other.path
  
  def __hash__(self):
    return (hash(self.request_method) * 397) ^ hash(self.path)
  
  def __str__(self):
    result = '%s %s' % (self.request_method, self.path)
    
    if len(self.additional_information) > 0:
      result += '\n%s' % (self.additional_information,)
    
    return result

def get(environment:dict, path_params:dict, query_params:dict, body):
  paths = set()
  
  nodes_to_process = [path_tries['interface']]
  while len(nodes_to_process) > 0:
    current_node = nodes_to_process.pop(0)
    
    for request_method in HTTPRequestMethods:
      if current_node.get_request_method_func(request_method) is None:
        continue
      
      paths.add(AvailablePath(str(request_method), current_node.get_pretty_path()))
    
    for child in current_node.get_children():
      nodes_to_process.append(child)
  
  return Response(paths, HTTPStatusCodes.HTTP200, use_base_field_in_xml=True, use_base_field_in_yaml=True)