
import contextlib


@contextlib.contextmanager
def suppress(*exceptions):
    """
    Context manager to suppress specific exceptions.

    :param exceptions: the exception types to suppress
    """
    try:
        yield
    except exceptions:
        pass


def raiser(exception=Exception):
    """
    Create a function that raises `exception` when invoked.

    This function can be used to quickly create a callback function that
    raises an exception. This is something a lambda expression cannot do
    since those cannot contain a ``raise`` statement.

    Any arguments that are passed to the returned function will be
    passed along to the exception's constructor.
    """
    def f(*args, **kwargs):
        raise exception(*args, **kwargs)
    return f


class Collector(object):

    def __init__(self, *exceptions):
        self._collectable_exceptions = exceptions

        self.exceptions = []

    def run(self, f, *args, **kwargs):
        with self:
            return f(*args, **kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, self._collectable_exceptions):
            self.exceptions.append(exc_val)
            return True

        # Not handled
        return False
