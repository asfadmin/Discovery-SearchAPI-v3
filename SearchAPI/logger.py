
import logging
import os
from pythonjsonlogger import jsonlogger


class ConsoleStreamFormatter(logging.Formatter):
    """
    Custom Logger formatter, used when running this app locally
    """
    class Colors:
        """
        I.e: print(f"{colors.WARNING} Some warning text here {colors.END}")
        """
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'

        WARNING = '\033[93m'
        ERROR = '\033[91m'

        HEADER = '\033[95m'
        BOLD = '\033[1m'
        BOLD_OFF = '\033[22m'
        UNDERLINE = '\033[4m'

        END = '\033[0m'

    LOGGER_FORMAT = f"{Colors.BOLD}[ %(asctime)s (%(name)s) %(filename)s:%(lineno)d ] %(levelname)s - {Colors.BOLD_OFF}%(message)s"

    FORMATS = {
        logging.DEBUG:      Colors.OKBLUE + LOGGER_FORMAT + Colors.END,
        logging.INFO:       Colors.OKCYAN + LOGGER_FORMAT + Colors.END,
        logging.WARNING:    Colors.WARNING + LOGGER_FORMAT + Colors.END,
        logging.ERROR:      Colors.ERROR + LOGGER_FORMAT + Colors.END,
        logging.CRITICAL:   Colors.ERROR + Colors.BOLD + LOGGER_FORMAT + Colors.END
    }

    def format(self, record: logging.LogRecord) -> logging.Formatter:
        # If it's bytes, turn it to a string:
        if isinstance(record.msg, bytes):
            record.msg = record.msg.decode("utf-8")
        # If the message is bigger than one line, give it it's own block, and indent a bit:
        if isinstance(record.msg, str) and record.msg.count('\n') > 0:
            msg_list = record.msg.split("\n")
            record.msg = "<multi-line>:\n\t" + "\n\t".join(msg_list)

        # Add color to each of the logging formats:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class AwsStreamFormatter(logging.Formatter):
    """
    Custom Logger formatter, used when running this app in AWS
    """
    LOGGER_FORMAT = " ".join([
        "%(asctime)s",
        "%(name)s",
        "%(pathname)s",
        "%(lineno)d",
        "%(levelname)s",
        "%(message)s",
        "%(aws_request_id)s",
    ])

    LOGGER_RENAME_FIELDS = {
        "asctime": "datetime",
        "lineno": "line_number",
        "levelname": "log_level",
    }

    def format(self, record: logging.LogRecord) -> logging.Formatter:
        formatter = jsonlogger.JsonFormatter(
            self.LOGGER_FORMAT,
            rename_fields=self.LOGGER_RENAME_FIELDS
        )
        return formatter.format(record)

def get_logger(name: str, level: int=logging.DEBUG) -> logging.Logger:
    """
    Builds and returns our custom logger for each sub-module
    """
    ## Clear the built in 'StreamHandler', to avoid duplicate messages:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    ## Setup what the format should look like, depending on if in AWS or local:
    stream_handle = logging.StreamHandler()
    # Default to false if not set:
    if os.environ.get('LOCAL_RUN', "FALSE").upper() == "TRUE":
        # You're running locally!
        stream_handle.setFormatter(ConsoleStreamFormatter())
    else:
        # You're running in Lambda!
        stream_handle.setFormatter(AwsStreamFormatter())

    ## Build the logger itself:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(stream_handle)

    ## Setup the asf logger real fast:
    asf_logger = logging.getLogger('asf_search')
    asf_logger.addHandler(stream_handle)
    asf_logger.setLevel(level)
    return logger
