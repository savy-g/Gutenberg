"""Utility methods to deal with command-line interfaces."""


import argparse
import contextlib
import itertools
import logging


LOG_FORMAT = r'%(levelname)s:%(asctime)s:%(message)s'


class ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that has a default logging/verbosity argument
    and sets the loglevel accordingly. The parser also customizes the
    log-record format string.

    """
    def __init__(self, *args, **kwargs):
        self.logformat = kwargs.pop('logformat', LOG_FORMAT)
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.add_argument('-v', '--verbose', action='count', default=0,
                          help='increase logging verbosity')

    def parse_args(self, *args, **kwargs):
        argv = argparse.ArgumentParser.parse_args(self, *args, **kwargs)
        logging.basicConfig(
            level=loglevel(argv.verbose),
            format=self.logformat,
        )
        return managed_namespace(argv)


def byte_size_type(argument):
    """Parses a string argument into a valid size in bytes.

    Args:
        argument (str): the argument to convert to a byte-size

    Returns:
        int: the number of bytes represented by the argument

    Examples:
        >>> byte_size_type('128kb')
        128000

        >>> byte_size_type('100.123 MB')
        100123000

        >>> byte_size_type('1 GB')
        1000000000

        >>> byte_size_type('100')  # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ArgumentTypeError: argument "100" does not end with a size specifier...

        >>> byte_size_type('foo KB')
        Traceback (most recent call last):
            ...
        ArgumentTypeError: argument "foo KB" is not a valid number

        >>> byte_size_type('1.3212 kb')
        Traceback (most recent call last):
            ...
        ArgumentTypeError: argument "1.3212 kb" is not an integral byte number

    """
    arg = argument.strip().lower()

    size_t = None
    for size_name in byte_size_type.size_names:
        if arg.endswith(size_name):
            size_t = size_name
            break
    else:
        raise argparse.ArgumentTypeError(
            'argument "%s" does not end with a size specifier '
            '(should be any of %s)'
            % (argument, ', '.join(byte_size_type.size_names)))

    num_bytes = arg[:len(arg) - len(size_t)].strip()
    try:
        num_bytes = float(num_bytes) * byte_size_type.size_conversion[size_t]
    except ValueError:
        raise argparse.ArgumentTypeError(
            'argument "%s" is not a valid number' % argument)

    if not num_bytes == int(num_bytes):
        raise argparse.ArgumentTypeError(
            'argument "%s" is not an integral byte number' % argument)

    return int(num_bytes)
byte_size_type.size_names = ['kb', 'mb', 'gb']
byte_size_type.size_mults = [10 ** 3, 10 ** 6, 10 ** 9]
byte_size_type.size_conversion = \
    dict(itertools.izip(byte_size_type.size_names, byte_size_type.size_mults))


@contextlib.contextmanager
def managed_namespace(args):
    """Context manager for argparse.Namespace objects that automatically closes
    all the files that were passed in as arguments.

    """
    yield args
    for argv in args.__dict__.itervalues():
        if isinstance(argv, file):
            argv.close()


def loglevel(logval):
    """Converts an integer into the appropriate logging level. Higher values
    lead to more detailed logging, lower values lead to less detailed logging.

    Args:
        logval (int): the integer value to convert into a logging level

    Returns:
        int: the logging level corresponding to the integer value

    Examples:
        >>> loglevel(-2) == logging.CRITICAL
        True

        >>> loglevel(-1) == logging.ERROR
        True

        >>> loglevel(0) == logging.WARNING
        True

        >>> loglevel(1) == logging.INFO
        True

        >>> loglevel(2) == logging.DEBUG
        True

        >>> loglevel(3) == logging.NOTSET
        True

        >>> loglevel(123) == logging.NOTSET
        True

        >>> loglevel(-123) == logging.CRITICAL
        True

    """
    stdlvl, maxlvl, minlvl = logging.WARNING, logging.CRITICAL, logging.NOTSET
    return min(maxlvl, max(minlvl, stdlvl - 10 * logval))