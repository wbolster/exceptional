
import contextlib
import functools


__all__ = [
    'suppress',
    'raiser',
    'Collector',
]


try:
    # Prefer the version in the stdlib
    suppress = contextlib.suppress
except AttributeError:
    # Fallback for Python < 3.4
    class suppress(object):
        """
        Context manager to suppress specified exceptions::

            with suppress(ValueError):
                do_something()

        This can also be used as a decorator:

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
        if exc_type is not None and issubclass(exc_type, self._collectable):
            self.exceptions.append(exc_val)
            return True

        # Not handled
        return False
