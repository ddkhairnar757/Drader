import logging
import tempfile
import unittest

from app.logs.logger import configure_logger, get_logger


class TestLogger(unittest.TestCase):
    def test_configure_logger_creates_logger(self) -> None:
        logger = configure_logger(level=logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(logger.name, "quant_research")

    def test_configure_logger_file_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = f"{temp_dir}/test.log"
            logger = configure_logger(log_file=log_path, level=logging.INFO)
            self.assertTrue(any(handler.baseFilename.endswith("test.log") for handler in logger.handlers if hasattr(handler, "baseFilename")))
            get_logger().info("test message")

            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
