import time
import logging


def try_to_execute(try_times, sleep_time):
    def decorator(func):
        def wrapper(*args, **kwargs):
            i = 0
            while i < try_times:
                try:
                    result = func(*args, **kwargs)
                    break
                except Exception as e:
                    logging.warning(e)
                    time.sleep(sleep_time)
                    i += 1

                    if i == try_times:
                        error_string = f'{func.__name__} failed {try_times} times with args:{args}, kwargs:{kwargs}'
                        logging.error(f'{func.__name__} failed {try_times} times with args:{args}, kwargs:{kwargs}')
                        print(error_string)
                        raise e
            return result

        return wrapper
    return decorator
