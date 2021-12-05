"""
Logger class
"""

from rich import print as rprint
from rich.console import Console
from rich.theme import Theme

import datetime
import os

class Logger:
    log_out_all = []
    log_err_all = []
    timestamp = "." + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    custom_theme = Theme({
        "info" : 'bold green',
        "note": "bold magenta",
        "warn": "bold yellow",
        "error": "bold red"
    })
    console = Console(theme = custom_theme)
    filename = 'out'

    def __init__(self, level=0):
        self.level = level

    def rule(self, *message):
        Logger.console.rule(*message)

    def print(self, *message):
        """
        Default print (without Text wrapper) to be able to print dicts and other stuff
        """
        Logger.log_out_all.extend([str(i) for i in message])
        rprint(*message)

    def info(self, *message, style=None):
        """
        Write to stdout
        """
        Logger.log_out_all.append(" ".join(['INFO:' + "".join([' ']*self.level), *message]))
        Logger.console.print('INFO:' + "".join([' ']*self.level), *message, style=style or 'info')
        self.write_out(Logger.filename, 'INFO: ' + ' '.join(message))

    def err(self, *message):
        """
        Write to "stderr"
        """
        Logger.log_err_all.append(" ".join(['ERROR:', *message]))
        Logger.console.print('ERROR:', *message, style='error')
        self.write_err(Logger.filename, 'ERROR: ' + ' '.join(message))

    def warn(self, *message):
        """
        Write to stderr
        """
        Logger.log_err_all.append(" ".join(['WARN:', *message]))
        Logger.console.print('WARN:', *message, style='warn')
        self.write_out(Logger.filename, 'WARN: ' + ' '.join(message))

    def note(self, *message):
        """
        Write to stderr
        """
        Logger.log_out_all.append(" ".join(['NOTE:', *message]))
        Logger.console.print('NOTE:', *message, style='note')
        self.write_out(Logger.filename, 'NOTE: ' + ' '.join(message))

    def die(self, *message, exception=RuntimeError):
        """
        Write to stderr, and die
        """
        self.err(*message)
        raise(exception(*message))

    def write_out(self, fname, message_str, timestamp=False):
        """
        write to output file
        """
        ts = Logger.timestamp if timestamp else ''
        with open(fname + ts + '.stdout.log', 'a') as outfile:
            outfile.write(message_str + '\n')

    def write_err(self, fname, messsage_str, timestamp=False):
        """
        write to output file
        """
        ts = Logger.timestamp if timestamp else ''
        with open(fname + ts + '.stderr.log', 'a') as errfile:
            errfile.write(messsage_str + '\n')

    def write_all(self, fname, timestamp=False):
        """
        write to files
        """
        ts = Logger.timestamp if timestamp else ''
        with open(fname + ts + '.stdout.log', 'w') as outfile:
            outfile.write("\n".join(self.log_out_all))
        with open(fname + ts + '.stderr.log', 'w') as errfile:
            errfile.write("\n".join(self.log_err_all))
