import logging
from logging.handlers import RotatingFileHandler

import copy
import logging

from colorama import Fore, Style

class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
        
    def format(self, record):
        record_copy = copy.copy(record)
        if record_copy.levelno in self.COLORS:
            record_copy.levelname = (f"{self.COLORS[record_copy.levelno]}"
                                f"{record_copy.levelname}{Style.RESET_ALL}")
            record_copy.msg = (f"{self.COLORS[record_copy.levelno]}"
                            f"{record_copy.msg}{Style.RESET_ALL}")
        return super().format(record_copy)
    


standard_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
detailed_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d', datefmt='%Y-%m-%d %H:%M:%S')


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ColoredFormatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    datefmt='%Y-%m-%d %H:%M:%S'
))


file_handler = RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5, encoding='utf8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(detailed_formatter)

error_file_handler = RotatingFileHandler('logs/errors.log', maxBytes=10485760, backupCount=5, encoding='utf8')
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(detailed_formatter)

