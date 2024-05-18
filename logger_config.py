from logging import config


class LoggerConfigurator:
    """DO NOT use this instance, ONLY CALL IT.

    Example:
        >>> from logging import getLogger
        >>> LoggerConfigurator()
        >>> logger = getLogger()
    """

    def __init__(self) -> None:
        self._LOG_CONFIG = {
            "version": 1,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console_formatter",
                    "stream": "ext://sys.stdout",
                },
                # "file": {
                #     "class": "logging.FileHandler",
                #     "filename": "app.log",
                #     "formatter": "file_formatter",
                # },
            },
            "formatters": {
                "console_formatter": {
                    "()": "colorlog.ColoredFormatter",
                    "format": "%(log_color)s[%(levelname)s]%(reset)s %(message)s",
                    "log_colors": {
                        "DEBUG": "green",
                        "INFO": "white",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "bold_red",
                    },
                },
                "file_formatter": {
                    "format": "%(asctime)s [%(levelname)-8s] )>- %(message)s",
                    "datefmt": "%m-%d %H:%M:%S",
                },
            },
            # "root": {"level": "DEBUG", "handlers": ["console", "file"]},
            # "root": {"level": "INFO", "handlers": ["console", "file"]},
            # "root": {"level": "DEBUG", "handlers": ["console"]},
            "root": {"level": "INFO", "handlers": ["console"]},
        }
        config.dictConfig(self._LOG_CONFIG)


# if __name__ == "__main__":
#     for_test = LoggerConfigurator()
#     logger = for_test.getLogger()
#     logger.debug("Logger verification test.")
#     logger.info("This is info")
#     logger.warning("This is warning")
#     logger.error("This is error")
#     logger.critical("This is critical")
