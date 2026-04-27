import pymysql

from api.util.config import get_config_value

from enum import Enum

host = get_config_value('db_host')
user_name = get_config_value('db_user')
user_pw   = get_config_value('db_user_password')
music_admin_name = get_config_value('db_music_admin')
music_admin_pw   = get_config_value('db_music_admin_password')
user_admin_name = get_config_value('db_user_admin')
user_admin_pw   = get_config_value('db_user_admin_password')
db_name = get_config_value('db_name')
charset = get_config_value('db_charset')

class MySQLUser(Enum):
  USER = (user_name, user_pw)
  MUSIC_ADMIN = (music_admin_name, music_admin_pw)
  USER_ADMIN = (user_admin_name, user_admin_pw)

class MySQLWrapper:
  def __init__(self, user:MySQLUser = MySQLUser.USER, commit_on_close:bool = True):
    grievances = []
    
    if not isinstance(user, MySQLUser):
      grievances.append('the MySQL user must be a MySQLUser.')
    
    if not isinstance(commit_on_close, bool):
      grievances.append('the "commit on close" flag must be a boolean.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    name = user.value[0]
    pw   = user.value[1]
    
    if host is None or name is None or pw is None or db_name is None or charset is None:
      raise ValueError('since some db connection info is missing, the user connection can\'t work.')
    
    self._connection = pymysql.connect(host='localhost', user=name, password=pw, db='audioid', charset=charset, cursorclass=pymysql.cursors.DictCursor)
    self._cursor = self._connection.cursor()
    self._commit_on_close = commit_on_close
  
  def __enter__(self):
    return self
  
  def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self._cursor.close()
    
    if self._commit_on_close:
      self._connection.commit()
    
    self._connection.close()
  
  def get_cursor(self) -> pymysql.cursors.DictCursor:
    return self._cursor
  
  def commit(self) -> None:
    self._connection.commit()

def get_cursor(user:MySQLUser = MySQLUser.USER) -> MySQLWrapper:
  return MySQLWrapper(user)