import sys
import logging


class AppLogger(logging.Logger):
    def __init__(self, name="server", log_level=logging.DEBUG):
        super().__init__(name)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.log_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        self.stream_handler.setFormatter(self.log_formatter)
        self.logger.addHandler(self.stream_handler)
