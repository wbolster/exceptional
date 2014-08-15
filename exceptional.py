
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
