# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING.
#
# ***** END LICENSE BLOCK *****

try:
    import curses
except ImportError:
    curses = None
from functools import wraps
import logging
import sys

logger = logging.getLogger('pika')
logger.setLevel(logging.WARN)

# Define these attributes as references to their logging counterparts
debug = logger.debug
error = logger.error
info = logger.info
warning = logger.warning

# Constants
DEBUG = logging.DEBUG
ERROR = logging.ERROR
INFO = logging.INFO
WARNING = logging.WARNING

# Default Level
LEVEL = INFO


def method_call(method):
    """
    Logging decorator to send the method and arguments to logger.debug
    """
    @wraps(method)
    def debug_log(*args, **kwargs):

        if logger.getEffectiveLevel() == DEBUG:

            # Get the class name of what was passed to us
            try:
                class_name = args[0].__class__.__name__
            except AttributeError:
                class_name = 'Unknown'
            except IndexError:
                class_name = 'Unknown'

            # Build a list of arguments to send to the logger
            log_args = list()
            for x in xrange(1, len(args)):
                log_args.append(args[x])
            if len(kwargs) > 1:
                log_args.append(kwargs)

            # If we have arguments, log them as well, otherwise just the method
            if log_args:
                logger.debug("%s.%s(%r) Called", class_name, method.__name__,
                             log_args)
            else:
                logger.debug("%s.%s() Called", class_name, method.__name__)

        # Actually execute the method
        return method(*args, **kwargs)

    # Return the debug_log function to the python stack for execution
    return debug_log


def setup(level=INFO, color=False):
    """
    Setup Pika logging, useful for console debugging and logging pika info,
    warning, and error messages.

    Parameters:

    - level: Logging level. One of DEBUG, ERROR, INFO, WARNING.
             Default: INFO
    - color: Use colorized output. Default: False
    """
    global curses

    if curses and not color:
        curses = None

    logging.basicConfig(level=level)
    logging.getLogger('pika').setLevel(level)

    if color and curses and sys.stderr.isatty():

        # Setup Curses
        curses.setupterm()

        # If we have color support
        if curses.tigetnum("colors") > 0:

            # Assign a FormatOutput Formatter to a StreamHandler instance
            for handler in logging.getLogger('').handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setFormatter(FormatOutput())
                    break


class FormatOutput(logging.Formatter):
    """
    Creates a colorized output format for logging that helps provide easier
    context in debugging
    """
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        color = curses.tigetstr("setaf") or curses.tigetstr("setf") or ""
        self._level = {DEBUG: curses.tparm(color, 6),
                       ERROR: curses.tparm(color, 1),
                       INFO: curses.tparm(color, 2),
                       WARNING: curses.tparm(color, 3)}
        self._reset = curses.tigetstr("sgr0")
        self._class = curses.tparm(color, 4)
        self._args = curses.tparm(color, 2)
        elements = ['%(levelname)-8s', '%(asctime)-24s', '#%(process)s']
        self._prefix = '[%s]' % ' '.join(elements)

    def format(self, record):
        #timestamp = datetime.datetime.fromtimestamp(record.created)
        #record.timestamp = timestamp.isoformat(' ')

        message = record.getMessage()
        record.asctime = self.formatTime(record)
        if message[-6:] == 'Called':
            parts = message.split(' ')
            call = parts[0].split('.')
            end_method = call[1].find('(')
            start_content = message.find('(') + 1
            message = '%s%s.%s%s(%s%s%s)' % (self._class,
                                             call[0],
                                             call[1][:end_method],
                                             self._reset,
                                             self._args,
                                             message[start_content:-8],
                                             self._reset)

        output = "%s%s%s %s" % (self._level.get(record.levelno,
                                                self._reset),
                                self._prefix % record.__dict__,
                                self._reset,
                                message)
        if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            output = output.rstrip() + "\n    " + record.exc_text
        return output
