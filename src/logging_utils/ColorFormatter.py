import logging
from typing import override

class ColorFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt, datefmt):
        super().__init__()
        self.custom_fmt = fmt
        self.datefmt = datefmt
        self.FORMATS = {
            logging.DEBUG : self.grey + self.custom_fmt + self.reset,
            logging.INFO : self.grey + self.custom_fmt + self.reset,
            logging.WARNING : self.yellow + self.custom_fmt + self.reset,
            logging.ERROR : self.red + self.custom_fmt + self.reset,
            logging.CRITICAL : self.bold_red + self.custom_fmt + self.reset,
        }

    @override
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)
