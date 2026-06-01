from dao.mysql_utils import get_cursor, MySQLUser
from models.db import MySQLMessage
from util.infrastructure.functions import get_type_name

def get_messages(message_id:int = None, message_content:str = None) -> list[MySQLMessage]:
  grievances = []
  
  if message_id is not None and not isinstance(message_id, int):
    grievances.append('a message id must be an integer; found a %s instead.' % (get_type_name(message_id), ))
  
  if message_content is not None and not isinstance(message_content, str):
    grievances.append('message content must be a string; found a %s instead.' % (get_type_name(message_content), ))
  
  if len(grievances) > 0:
    raise TypeError('\n'.join(grievances))
  
  query = 'SELECT id, content FROM mysql_messages'
  
  where_predicates = []
  args = []
  if isinstance(message_id, int):
    where_predicates.append('id = %s')
    args.append(message_id)
  
  if isinstance(message_content, str):
    where_predicates.append('content LIKE %s')
    args.append('%s%s%s' % ('%', message_content, '%'))
  
  if len(where_predicates) > 0:
    query += '\nWHERE %s' % (' AND '.join(where_predicates))
  
  query += '\nORDER BY id;'
  
  args = tuple(args)
  
  result = []
  
  with get_cursor() as cursor:
    message_count = cursor.get_cursor().execute(query, args)
    for i in range(message_count):
      db_result = cursor.get_cursor().fetchone()
      result.append(MySQLMessage(db_result['id'], db_result['content']))
  
  return result

def save_message(mysql_message:MySQLMessage) -> MySQLMessage:
  if not isinstance(mysql_message, MySQLMessage):
    raise TypeError('a mysql message must be a MySQLMessage.')
  
  query = 'INSERT INTO mysql_messages (content) VALUES (%s)'
  args = (mysql_message.get_content(), )
  
  message_id = None
  with get_cursor(MySQLUser.USER_ADMIN) as cursor:
    cursor.get_cursor().execute(query, args)
    
    message_id = cursor.get_cursor().lastrowid
  
  return MySQLMessage(message_id, mysql_message.get_content())