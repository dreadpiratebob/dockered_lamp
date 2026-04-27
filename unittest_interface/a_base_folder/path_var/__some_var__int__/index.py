from api.util.http import HTTPStatusCodes, Response
def get(environment:dict, headers:dict, path_params:dict, query_params:dict, body) -> Response:
  return Response('debug: no.', HTTPStatusCodes.HTTP501)