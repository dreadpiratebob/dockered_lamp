from api.util.functions import get_search_text_from_raw_text

import datetime
import os.path

from enum import Enum

_log_dir = '/var/log/audioid/'

class LogLevel(Enum):
  DEBUG = ('debug', 0)
  INFO  = ('info', 1)
  WARN  = ('warn', 2)
  ERROR = ('error', 3)

class Logger:
  def __init__(self, log_level:LogLevel, log_dir:str = None):
    grievances = []
    
    if not isinstance(log_level, LogLevel):
      grievances.append('a log level must be a LogLevel.')
    
    if log_dir is not None and not isinstance(log_dir, str):
      grievances.append('a dir name must be a str.')
    
    if len(grievances) > 0:
      raise TypeError('\n'.join(grievances))
    
    if log_dir is None:
      log_dir = _log_dir
    
    log_dir = log_dir.replace('\\', '/')
    
    if log_dir[-1] != '/':
      log_dir += '/'
    
    self._log_level = log_level
    self._log_dir   = log_dir
  
  def debug(self, message:str):
    self.log(LogLevel.DEBUG, message)
  
  def info(self, message:str):
    self.log(LogLevel.INFO, message)
  
  def warn(self, message:str):
    self.log(LogLevel.WARN, message)
  
  def error(self, message:str):
    self.log(LogLevel.ERROR, message)
  
  def log(self, log_level:LogLevel, message:str):
    if log_level.value[1] < self._log_level.value[1]:
      return
    
    lcase, no_diacritics, lcase_no_diacritics = get_search_text_from_raw_text(str(message))
    
    now = datetime.datetime.utcnow()
    fmt_msg = '%s [%s]: %s' % (str(now), log_level.value[0], no_diacritics)
    print(fmt_msg)
    
    if not os.path.exists(_log_dir):
      os.makedirs(_log_dir)
    
    with open(self._log_dir + 'out.log', 'a+') as file_object:
      file_object.write("\n" + fmt_msg)

loggers = {LogLevel.DEBUG: {}, LogLevel.INFO: {}, LogLevel.WARN: {}, LogLevel.ERROR: {}}
def get_logger(log_level = LogLevel.DEBUG, log_dir = _log_dir):
  global loggers
  
  if log_dir in loggers[log_level].keys():
    return loggers[log_level][log_dir]
  
  logger = Logger(log_level, log_dir)
  loggers[log_level][log_dir] = logger
  
  return logger

def log_exception(exception:Exception) -> None:
  exception_type = str(type(exception))[8:-2]
  message = 'caught an exception of type ' + exception_type + '.\n'
  message += 'exception message: ' + str(exception) + '\n'
  message += 'stack trace:\n'
  
  exception_traceback = exception.__traceback__
  while exception_traceback is not None:
    filename = str(exception_traceback.tb_frame.f_code.co_filename)
    exception_line_number = str(exception_traceback.tb_lineno)
    message += '--from file ' + filename + ', line number ' + exception_line_number + '\n'
    
    exception_traceback = exception_traceback.tb_next
  
  get_logger().error(message)
