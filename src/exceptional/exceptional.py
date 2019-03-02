import functools


class ExceptionSuppressor:
    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        return exc_type is not None and issubclass(exc_type, self._exceptions)

    def __repr__(self):
        formatted = ", ".join(exc.__name__ for exc in self._exceptions)
        return "suppress({})".format(formatted)

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped(*args, **kwds):
            with self:
                return f(*args, **kwds)

        return wrapped


def suppress(*exceptions):
    """
    Suppress the specified exception(s).

    Both a context manager and a decorator.
    """
    return ExceptionSuppressor(*exceptions)


def collect(*exceptions):
    """
    Create a collector for the specified exceptions, when used as a context manager.
    """
    return Collector(*exceptions)


class Collector(object):
    """
    Exception collectiong helper.

    Use as a context manager; iterate to access the collected exceptions.
    """

    def __init__(self, *exceptions):
        self._exceptions = exceptions
        self._collected_exceptions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        elif issubclass(exc_type, self._exceptions):
            self._collected_exceptions.append(exc_val)
            return True
        else:
            return False

    def __repr__(self):
        formatted = ", ".join(exc.__name__ for exc in self._exceptions)
        return "collect({})".format(formatted)

    def __iter__(self):
        yield from self._collected_exceptions


def raiser(exception=Exception, *args, **kwargs):
    """
    Create a callable that will immediately raise `exception` when called.

    Arguments, if any, will be passed along to the exception's constructor.
    """
    return Raiser(exception, args, kwargs)


class Raiser:
    """
    Exception raising helper.
    """

    def __init__(self, exception_class, exception_args, exception_kwargs):
        self.exception_class = exception_class
        self.exception_args = exception_args
        self.exception_kwargs = exception_kwargs

    def __call__(self, *_args, **_kwargs):
        exc = self.exception_class(*self.exception_args, **self.exception_kwargs)
        raise exc

    def __repr__(self):
        name = self.exception_class.__qualname__
        if self.exception_args or self.exception_kwargs:
            return "raiser({}, ...)".format(name)
        else:
            return "raiser({})".format(name)
