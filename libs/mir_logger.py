import logging

# Get the logger instance
mir_logger = logging.getLogger('Mir')

# Set the logging level for this specific logger
mir_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s [%(levelname)s] | %(filename)s:%(lineno)s | %(funcName)s()\n  (%(asctime)s) %(message)s", datefmt="%H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
mir_logger.addHandler(console_handler)
