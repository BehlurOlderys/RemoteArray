from datetime import datetime
import os
import logging


def add_log(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    mainHandler = logging.FileHandler(name+".log")
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    mainHandler.setFormatter(formatter)
    log.addHandler(mainHandler)
    return log


class DefaultCaptureFilenameGenerator:
    def __init__(self, prefix):
        self._last_dir = None
        self._number = 0
        self._prefix = prefix

    def generate(self):
        current_day = datetime.now().strftime("%Y-%m-%d")
        new_dir = os.path.join(os.getcwd(), "capture", current_day)

        if self._last_dir is None or (self._last_dir != new_dir):
            self._last_dir = new_dir
            if not os.path.isdir(self._last_dir):
                os.makedirs(self._last_dir)

        dt_string = datetime.now().strftime("_%Y%m%d_%H%M%S")
        fn = self._prefix + dt_string + "_Capture_{0:05d}.tif".format(self._number)
        fp = os.path.join(self._last_dir, fn)
        self._number += 1
        return fp


class DefaultServerTransactionIDGenerator:
    def __init__(self):
        self._counter = 0

    def generate(self):
        r = self._counter
        self._counter += 1
        return r
