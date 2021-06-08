import logging

from library import backend


def test_set_logger():
    logger = logging.getLogger("Test Check")
    logger = backend.set_logger(logger, "booru-dl.log")
    assert type(logger) == logging.Logger
