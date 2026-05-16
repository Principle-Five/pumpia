"""
Simple logging to be used throughout pumpia.
"""

import logging


def _configure_logger():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)


logger = logging.getLogger(__name__)
_configure_logger()
