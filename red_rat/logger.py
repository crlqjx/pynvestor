import os
import logging
import functools
import datetime as dt


class Logger:
    def __init__(self):
        self._path = os.path.abspath(__file__)
        self._dir_path = os.path.dirname(self._path)

        self.log = logging.getLogger('RED_RAT')
        self.log.setLevel(logging.DEBUG)

        formatter = logging.Formatter(fmt='%(asctime)s|%(name)s|%(levelname)s:%(message)s',
                                      datefmt='%m/%d/%Y %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)

        file_handler = logging.FileHandler(os.path.join(self._dir_path, "debug.log"))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)

    def __call__(self, func):
        @functools.wraps(func)
        def with_logging(*args, **kwargs):
            try:
                self.log.debug(f"{func.__name__}")
                timer_start = dt.datetime.now()
                result = func(*args, **kwargs)
                timer_end = dt.datetime.now()
                timer = timer_end - timer_start
                self.log.debug(f"executed {func.__name__} in {round(timer.total_seconds(), 2)} seconds")
                return result
            except Exception as e:
                self.log.critical(f"Exception {type(e)}: {str(e)}")
                raise e
        return with_logging
