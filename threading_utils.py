import logging
import threading
import time

from telebot.apihelper import ApiTelegramException

_TIMEOUT_LOCK = threading.Lock()


def get_timeout_retry(e: ApiTelegramException):
  retry_after_text = "retry after "
  retry_text_pos = e.description.find(retry_after_text)
  if retry_text_pos < 0:
    return 0
  retry_amount_str = e.description[retry_text_pos + len(retry_after_text):]
  i = 0
  for num in retry_amount_str:
    if num in "0123456789":
      i += 1
    else:
      break
  return int(retry_amount_str[:i])


def timeout_error_lock(func):
  def inner_function(*args, **kwargs):
    with _TIMEOUT_LOCK:
      while True:
        try:
          return func(*args, **kwargs)
        except ApiTelegramException as E:
          if E.error_code == 429:
            timeout = get_timeout_retry(E)
            logging.exception(
                f"Too many requests error in {func.__name__}, retry in: {timeout}")
            time.sleep(timeout)
            continue
          raise E
  return inner_function
