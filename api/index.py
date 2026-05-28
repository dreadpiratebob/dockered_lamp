#!/usr/bin/python3.9
from os import path
import sys

from setuptools.package_index import user_agent

base_path = path.dirname(__file__)
sys.path.append(path.realpath(base_path))

from exceptions.http_base import \
  BadRequestException, \
  MethodNotAllowedException
from util.logger import get_logger
from util.http import \
  default_text_HTTPMIMEType, \
  text_HTTPMIMETypes, get_response_payload_as_bytes
from models.factories.response_factory import build_http_response_from_exception
from models.http import MajorHTTPMIMETypes, HTTPMIMETypes, HTTPHeaders, HTTPStatusCodes, HTTPRequestMethods, \
  HTTPRequestMethods_by_name, Message, Response
from util.http_path import \
  get_and_validate_rel_path, \
  default_interface_dir, \
  path_tries
from util.functions import get_type_name

from inspect import signature
from types import GeneratorType
from urllib.parse import parse_qs

bytes_encoding = 'UTF-8'

_cors_headers = \
{
  'Access-Control-Allow-Headers': 'access-control-allow-origin, accept, authorization, content-type, user-agent',
  'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
}

def get_and_validate_request_method(environment:dict):
  given_method = environment['REQUEST_METHOD'].lower()
  result = HTTPRequestMethods_by_name.get(given_method, None)
  
  if result is None:
    query_string = environment['QUERY_STRING']
    rel_path = environment['REQUEST_URI']
    if len(query_string) > 0:
      rel_path = rel_path[:-1 * (len(query_string) + 1)]
    
    raise MethodNotAllowedException(given_method, rel_path)
  
  return result

def get_and_validate_query_params(environment:dict):
  query_string = environment['QUERY_STRING']
  query_params = {}
  if len(query_string) > 0:
    try:
      query_params = parse_qs(query_string, keep_blank_values=True, strict_parsing=True)
    except ValueError as e:
      raise BadRequestException(str(e))
    
    query_params = {param: query_params[param][0] for param in query_params}
  
  return query_params

def get_request_body(environment:dict):
  if 'CONTENT_LENGTH' not in environment or 'wsgi.input' not in environment:
    return None
  
  # the environment variable CONTENT_LENGTH may be empty or missing
  try:
    request_body_size = int(environment.get('CONTENT_LENGTH', 0))
  except ValueError:
    return None # no request body was found
  
  return environment['wsgi.input'].read(request_body_size)

def get_contents(environment, headers):
  not_found_text = '<not found>'
  remote_addr = environment.get('REMOTE_ADDR', not_found_text)
  remote_port = environment.get('REMOTE_PORT', not_found_text)
  user_agent = environment.get('HTTP_USER_AGENT', not_found_text)
  
  printable_request_info = 'remote address / port: %s:%s\n' \
                           'user agent: %s\n' \
                           'headers:\n' % (remote_addr, remote_port, user_agent)
  keys = [key for key in headers]
  keys.sort()
  if len(keys) == 0:
    printable_request_info += '  (none)\n'
  for key in keys:
    printable_request_info += '  * %s: %s\n' % (key, headers[key])
  
  request_method = get_and_validate_request_method(environment)
  printable_request_info += 'request method: %s\n' % (request_method, )
  
  fail = False
  error_message = None
  response_code = None
  rel_path_data = None
  try:
    rel_path_data = get_and_validate_rel_path(environment)
    printable_request_info += 'relative path: %s\npath params:\n' % (rel_path_data.path_node.get_pretty_path()[len('/interface'):], )
    if len(rel_path_data.path_parameters) == 0:
      printable_request_info += '  (none)\n'
    for param_name in rel_path_data.path_parameters:
      printable_request_info += '  * %s: %s\n' % (param_name, rel_path_data.path_parameters[param_name])
  except Exception as e:
    printable_request_info += 'trying to resolve the path "%s"\ncaught exception: %s\n' % (environment['REQUEST_URI'], e)
    error_message = str(e)
    response_code = HTTPStatusCodes.HTTP400
    fail = True
  
  query_params = get_and_validate_query_params(environment)
  printable_request_info += 'query params:\n'
  if len(query_params) == 0:
    printable_request_info += '  (none)\n'
  for param_name in query_params:
    printable_request_info += '  * %s: %s\n' % (param_name, query_params[param_name])
  
  body = get_request_body(environment)
  printable_request_info += 'body: %s' % (None if body is None else body.decode(), )
  
  get_logger().debug(printable_request_info)
  
  accept = headers.get(HTTPHeaders.ACCEPT, None)
  content_type = None
  content_type_failure = False
  if rel_path_data is None:
    if accept.major_type == MajorHTTPMIMETypes.APPLICATION or accept.major_type == MajorHTTPMIMETypes.TEXT:
      content_type = accept
    else:
      content_type = HTTPMIMETypes.APPLICATION_YAML
  elif accept is None or accept == HTTPMIMETypes.STAR_STAR:
    content_type = rel_path_data.path_node.get_request_method_default_content_type(request_method)
  elif accept in rel_path_data.path_node.get_request_method_allowed_content_types(request_method):
    content_type = accept
  else:
    content_type_failure = True
    content_type = HTTPMIMETypes.APPLICATION_YAML
  
  if fail:
    return Response(error_message, response_code, mime_type=content_type)
  
  if request_method == HTTPRequestMethods.OPTIONS:
    return Response('', HTTPStatusCodes.HTTP200, mime_type=content_type, headers=_cors_headers)
  
  if content_type_failure:
    content = 'unsupported value for the Accept header; accepted values are: %s' % (', '.join([str(content_type) for content_type in rel_path_data.path_node.get_request_method_allowed_content_types(request_method)]), )
    return Response(content, HTTPStatusCodes.HTTP400, mime_type=content_type)
  
  rel_path = rel_path_data.path_node.get_pretty_path()[len(default_interface_dir)+1:]
  if len(rel_path) == 0:
    rel_path = '/'
  
  exec_func = rel_path_data.path_node.get_request_method_func(request_method)
  method_is_good = True
  if exec_func is None:
    method_is_good = False
  
  endpoint_sig = '%s %s' % (str(request_method).upper(), rel_path)
  try:
    sig = signature(exec_func)
    if len(sig.parameters) != 5:
      get_logger().warn('%s has the wrong number of parameters.' % (endpoint_sig, ))
      method_is_good = False
  except TypeError:
    get_logger().warn('%s isn\'t callable.' % (endpoint_sig, ))
    method_is_good = False
  
  response = None
  if method_is_good:
    response:Response = exec_func(preprocess_request(environment, None if body is None else body.decode()), headers, rel_path_data.path_parameters, query_params, body)
    
    if request_method == HTTPRequestMethods.OPTIONS:
      response.upsert_headers(_cors_headers)
    
  elif request_method == HTTPRequestMethods.OPTIONS:
    response = Response('', HTTPStatusCodes.HTTP200, mime_type=content_type, headers=_cors_headers)
  else:
    raise MethodNotAllowedException(str(request_method), rel_path)
  
  if response.get_mime_type() is None:
    response.set_mime_type(content_type)
  
  return response

def preprocess_request(environment:dict, body:str):
  environment['root_path_node'] = path_tries['interface']
  return environment

def application(environment, start_response):
  response = Response(Message('no.'), HTTPStatusCodes.HTTP501)
  headers = { HTTPHeaders.ACCEPT: HTTPHeaders.ACCEPT.get_value(environment) }
  
  try:
    headers = { header: header.get_value(environment) for header in HTTPHeaders }
    obj = get_contents(environment, headers)
    if isinstance(obj, Response):
      response = obj
    else:
      raise TypeError('got an invalid response type of %s.' % (type(obj), ))
  except Exception as e:
    message = 'caught a(n) %s: %s' % (get_type_name(e), str(e))
    exception_traceback = e.__traceback__
    while exception_traceback is not None:
      filename = str(exception_traceback.tb_frame.f_code.co_filename)
      exception_line_number = str(exception_traceback.tb_lineno)
      message += '\n  --from file %s, line number %s' % (filename, exception_line_number)
      
      exception_traceback = exception_traceback.tb_next
    
    get_logger().debug(message)
    
    response = build_http_response_from_exception(e)
    if headers[HTTPHeaders.ACCEPT] not in text_HTTPMIMETypes:
      response.set_mime_type(default_text_HTTPMIMEType)
  
  output = get_response_payload_as_bytes(response, bytes_encoding)
  content_length = len(output) if response.get_content_length() is None else response.get_content_length()
  
  if not isinstance(output, GeneratorType):
    output = [output]
  
  status = str(response.get_status_code())
  
  headers = \
  {
    'Content-Type': str(response.get_mime_type()),
    'Content-Length': str(content_length),
    'Access-Control-Allow-Origin': '*'
  }
  
  for key in response.get_headers():
    if key not in headers:
      headers[key] = response.get_headers()[key]
  
  headers = [(key, headers[key]) for key in headers]
  
  start_response(status, headers)
  
  return output