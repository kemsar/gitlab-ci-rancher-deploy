import warnings

import click
import sys
import os
from enum import IntEnum
from datetime import datetime

datetime_string_format = '%Y-%m-%d %H:%M:%S.%f'


class LogLevel(IntEnum):
    """The LogLevel class is an Enum to define available and set current logging levels."""
    TRACE = 6
    DEBUG = 5
    INFO = 4
    WARN = 3
    ERROR = 2
    FATAL = 1
    SILENT = 0


class Logger:
    """A class to manage and write log messages."""

    def __init__(self, log_level=LogLevel.INFO, name='DefaultLogger', filter_deprecated=True):
        """
        Logger constructor.

        :param log_level: The desired level of logging output. OPTIONAL. Defaults to LogLevel.INFO.
        :param name: The identifier for this Logger. OPTIONAL. Defaults to 'DefaultLogger'
        """
        if isinstance(log_level, str):
            try:
                self.level = LogLevel[log_level.upper()]
            except KeyError:
                self.level = LogLevel.INFO
        else:
            self.level = log_level
        self.name = name
        self.__trace_cache = {}
        if filter_deprecated:
            warnings.filterwarnings("ignore", category=DeprecationWarning)
        click.echo("")

    def trace(self, message, cache=None):
        if self.level >= LogLevel.TRACE:
            timestamp = datetime.now().strftime(datetime_string_format)
            if cache is not None:
                self.__trace_cache[timestamp] = cache
            click.echo(click.style(timestamp +
                                   ' [TRACE] ' + self.name + ' ' + message, fg='white', dim=True))

    def debug(self, title, content=''):
        if self.level >= LogLevel.DEBUG:
            click.echo(click.style(datetime.now().strftime(datetime_string_format) +
                                   ' [DEBUG] ' + self.name + ' ' + title.rjust(25) + ':  ' + content,
                                   fg='white', bg='blue'))

    def info(self, message):
        if self.level >= LogLevel.INFO:
            click.echo(click.style(datetime.now().strftime(datetime_string_format) +
                                   ' [INFO] ' + self.name + ' ' + message, fg='green'))

    def warn(self, message):
        if self.level >= LogLevel.WARN:
            click.echo(click.style(datetime.now().strftime(datetime_string_format) +
                                   ' [WARN] ' + self.name + ' ' + message, fg='yellow'))

    def error(self, message):
        if self.level >= LogLevel.ERROR:
            click.echo(click.style(datetime.now().strftime(datetime_string_format) +
                                   ' [ERROR] ' + self.name + ' ' + message, fg='red'))

    def fatal(self, message):
        if self.level >= LogLevel.FATAL:
            click.echo(click.style(datetime.now().strftime(datetime_string_format) +
                                   ' [FATAL] ' + self.name + ' ' + message, fg='bright_white', bg='red', bold=True))
        sys.exit('Fatal Error: %s' % message)

    def trace_dump(self):
        if self.level >= LogLevel.TRACE:
            for line in self.__trace_cache:
                key, value = line
                click.echo(click.style(key +
                                       ' [TRACE_CACHE_DUMP] ' + self.name + ' ' + value, fg='white', dim=True))
            self.__trace_cache = {}
