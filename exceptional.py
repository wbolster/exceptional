
import functools


__all__ = [
    'suppress',
    'raiser',
    'Collector',
]


# XXX: Do not use the contextlib.suppress() from the stdlib, since
# that version (as of Python 3.4) cannot be used as a decorator.
class suppress(object):
    """
    Suppress the specified exceptions.

    This can be used as a context manager::

        with suppress(ValueError):
            do_something()

    Additionally, this can be used as a decorator:

        @suppress(ValueError):
        def do_something():
            pass
    """
    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        return (exc_type is not None
                and issubclass(exc_type, self._exceptions))

    def __call__(self, func):
        @functools.wraps(func)
        def wrapped(*args, **kwds):
            with self:
                return func(*args, **kwds)

        return wrapped


def raiser(exception=Exception, *args, **kwargs):
    """
    Create a function that raises `exception` when invoked.

    This can be used to quickly create a callback function that raises
    an exception. This is something a lambda expression cannot do since
    those cannot contain a ``raise`` statement.

    Any additional arguments (both positional and keyword) passed to
    this function will be passed along to the exception's constructor.

    The returned function will accept (and ignore) any arguments, making
    it suitable for use as a callback, regardless of the expected
    signature.
    """
    def f(*_, **__):
        raise exception(*args, **kwargs)
    return f


class Collector(object):

    def __init__(self, *exceptions):
        self._collectable = exceptions
        self.exceptions = []

    def run(self, f, *args, **kwargs):
        with self:
            return f(*args, **kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):

        if exc_type is None:
            return True  # no exception happened at all

        if not isinstance(exc_val, exc_type):
            # This happens with Python 2.6, see
            # http://bugs.python.org/issue7853
            exc_val = exc_type(exc_val)

        if issubclass(exc_type, self._collectable):
            self.exceptions.append(exc_val)
            return True  # handled

        return False  # not handled
