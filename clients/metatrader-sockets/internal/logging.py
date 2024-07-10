import sys
import logging
from colorlog import ColoredFormatter


class Logger(logging.Logger):
    """
    Custom logger for application logging with colored console output and optional file logging.

    Args:
        name (str, optional): Logger name. Defaults to __name__.
        log_level (int, optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to logging.DEBUG.
        filename (str, optional): File to log messages to. Defaults to "" (no file logging).

    Attributes:
        stream_handler (logging.StreamHandler): Handler for console output with colored formatting.
        file_handler (logging.FileHandler, optional): Handler for file output if filename is provided.
        log_formatter (ColoredFormatter): Formatter for log messages with colored output.

    Usage:
        logger = AppLogger(name='my_logger', log_level=logging.INFO, filename='app.log')

        logger.info('This is an info message.')

        logger.error('This is an error message.')

    """

    def __init__(
        self,
        name=__name__,
        log_level=logging.DEBUG,
        filename: str = "",
    ):
        super().__init__(name, level=log_level)

        # Colored formatter for console logging
        self.log_formatter = ColoredFormatter(
            "[MetaTrader Terminal Server] %(process)d - %(asctime)s  %(log_color)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d, %I:%M:%S %p",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )

        # Stream handler for console logging with colored output
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.stream_handler.setFormatter(self.log_formatter)
        self.addHandler(self.stream_handler)

        # File handler for file logging if filename is supplied
        if filename:
            self.file_handler = logging.FileHandler(filename)
            self.file_handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )
            self.addHandler(self.file_handler)

        self.propagate = False  # Prevent propagation to parent logger


# # Example usage:
# if __name__ == "__main__":
#     # Example usage
#     logger = AppLogger(name="my_app", log_level=logging.DEBUG, filename="app.log")
#     logger.debug("Debug message")
#     logger.info("Info message")
#     logger.warning("Warning message")
#     logger.error("Error message")
#     logger.critical("Critical message")


# format = "%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
# format="%(asctime)s %(levelname)s %(message)s",
# datefmt = '%Y-%m-%d %H:%M:%S',
