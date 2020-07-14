import unittest


def msg_output(logger):
    logger.trace('LogLevel: ' + logger.level.name)
    logger.debug('LogLevel: ' + logger.level.name)
    logger.info('LogLevel: ' + logger.level.name)
    logger.warn('LogLevel: ' + logger.level.name)
    logger.error('LogLevel: ' + logger.level.name)
    logger.fatal('LogLevel: ' + logger.level.name)


class LoggerTestCase(unittest.TestCase):

    def test_logger(self):
        from logger import Logger
        logger = Logger('deug')
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_trace(self):
        print('============= TRACE =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.TRACE)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_debug(self):
        print('============= DEBUG =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.DEBUG)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_info(self):
        print('============= INFO =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.INFO)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_warn(self):
        print('============= WARN =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.WARN)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_error(self):
        print('============= ERROR =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.ERROR)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_fatal(self):
        print('============= FATAL =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.FATAL)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)

    def test_logger_silent(self):
        print('============= SILENT =============')
        from logger import Logger
        from logger import LogLevel
        logger = Logger(LogLevel.SILENT)
        with self.assertRaises(SystemExit) as cm:
            msg_output(logger)
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
