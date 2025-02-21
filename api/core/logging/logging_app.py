import logging

from api.core.logging.logging_handlers import console_handler
from api.core.logging.logging_handlers import error_file_handler
from api.core.logging.logging_handlers import file_handler


class SensitivaDataFilter(logging.Filter):
    def filter(self, record):
        return not any(
            word in record.getMessage().lower()
            for word in ["password", "token", "secret"]
        )


logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_file_handler)
logger.addFilter(SensitivaDataFilter())


if __name__ == "__main__":
    logger.error("test")
