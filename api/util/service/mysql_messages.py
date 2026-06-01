from models.http import FormParams

class MySQLMessageQueryParams(FormParams):
  CONTENT_FILTER = 'content', False, str, 'string', 'a string', None, 'only include messages with this string in their contents.'