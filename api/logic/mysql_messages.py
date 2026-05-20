from dao.db import get_messages
from models.db import MySQLMessage

def get_mysql_message(message_id:int) -> MySQLMessage:
  if not isinstance(message_id, int):
    raise TypeError('a message id must be an integer.')
  
  messages = get_messages(message_id)
  if len(messages) == 0:
    return None
  
  if len(messages) > 1:
    raise ValueError('%s messages were found with the id %s.' % (len(messages), message_id))
  
  return messages[0]

def get_mysql_messages(content_filter:str) -> list[MySQLMessage]:
  return get_messages(message_id=None, message_content=content_filter)