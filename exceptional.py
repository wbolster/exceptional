
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


class Collector(object):

    def __init__(self, *exceptions):
        self._except_clause = exceptions

        self.exceptions = []

    def run(self, f, *args, **kwargs):
        try:
            return f(*args, **kwargs)
        except self._except_clause as exc:
            self.exceptions.append(exc)
