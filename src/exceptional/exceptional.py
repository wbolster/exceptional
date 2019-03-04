import collections
import contextlib
import inspect
import operator


def escape_format_string(s):
    return s.replace("{", "{{").replace("}", "}}")


class Missing:
    def __repr__(self):
        return "<MISSING>"


MISSING = Missing()


def suppress(*exceptions):
    """
    Suppress the specified exception(s).

    This can be used as a context manager or as a decorator.
    """
    return ExceptionSuppressor(*exceptions)


class ExceptionSuppressor(contextlib.ContextDecorator):
    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        return exc_type is not None and issubclass(exc_type, self._exceptions)

    def __repr__(self):
        formatted = ", ".join(exc.__name__ for exc in self._exceptions)
        return "{}.suppress({})".format(__package__, formatted)


def collect(*exceptions):
    """
    Create a collector for the specified exceptions, when used as a context manager.
    """
    return ExceptionCollector(*exceptions)


class ExceptionCollector:
    """
    Exception collectiong helper.

    This should be used as a context manager. Iterate over this object to
    access the collected exceptions.
    """

    def __init__(self, *exceptions):
        self._exceptions = exceptions
        self._collected_exceptions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return True
        elif issubclass(exc_type, self._exceptions):
            self._collected_exceptions.append(exc_value)
            return True
        else:
            return False

    def __repr__(self):
        formatted = ", ".join(exc.__name__ for exc in self._exceptions)
        return "{}.collect({})".format(__package__, formatted)

    def __iter__(self):
        yield from self._collected_exceptions


def is_exception(x):
    return inspect.isclass(x) and issubclass(x, BaseException)


def is_multiple_exceptions(x):
    return isinstance(x, (tuple, list)) and all(is_exception(item) for item in x)


def wrap(
    original_or_mapping,
    replacement=None,
    *,
    message=MISSING,
    prefix=None,
    format=None,
    set_cause=True,
    suppress_context=False
):
    """
    Raise a replacement exception wrapping the original exception.

    This can be used as a context manager or as a decorator.
    """
    if isinstance(original_or_mapping, collections.Mapping):
        if replacement is not None:
            raise TypeError(
                "cannot specify both a mapping and a replacement exception type"
            )
        items = original_or_mapping.items()
    else:
        original = original_or_mapping
        items = [(original, replacement)]

    mapping = {}
    for original, replacement in items:
        if not is_exception(replacement):
            raise TypeError("not an exception class: {!r}".format(replacement))
        if is_exception(original):
            mapping[original] = replacement
        elif is_multiple_exceptions(original):
            for exc in original:
                mapping[exc] = replacement
        else:
            raise TypeError("not an exception class (or tuple): {!r}".format(original))

    expressions = [
        message not in (None, MISSING),
        prefix is not None,
        format is not None,
    ]
    if sum(expressions) > 1:
        raise TypeError("specify at most one of 'message', 'prefix', or 'format'")

    if format is not None:
        pass
    elif prefix is not None:
        format = escape_format_string(prefix) + ": {}"
    elif message is MISSING:
        format = "{}"
    elif message is not None:
        format = escape_format_string(message)

    return ExceptionWrapper(mapping, format, set_cause, suppress_context)


class ExceptionWrapper(contextlib.ContextDecorator):
    """
    Exception wrapping helper.

    This can be used as a context manager or as a decorator.
    """

    def __init__(self, mapping, format, set_cause, suppress_context):
        self._mapping = mapping
        self._format = format
        self._set_cause = set_cause
        self._suppress_context = suppress_context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            # No exception occurred.
            return True

        replacement_exc_class = self._find_replacement_exception_class(exc_type)
        if replacement_exc_class is not None:
            if self._format is None:
                exc = replacement_exc_class()
            else:
                exc = replacement_exc_class(self._format.format(exc_value))
            if self._set_cause:
                exc.__cause__ = exc_value
            if self._suppress_context:
                exc.__suppress_context__ = True
            raise exc

        return False  # Cannot be handled here.

    def _find_replacement_exception_class(self, exception_class):
        for cls in exception_class.mro():
            try:
                return self._mapping[cls]
            except KeyError:
                pass
        else:
            return None

    def __repr__(self):
        if not self._mapping:
            formatted = "{}"
        elif len(self._mapping) == 1:
            original, new = next(iter(self._mapping.items()))
            formatted = "{}, {}".format(original.__name__, new.__name__)
        else:
            original = min(self._mapping.keys(), key=operator.attrgetter("__name__"))
            new = self._mapping[original]
            formatted = "{{{}: {}, ...}}".format(original.__name__, new.__name__)

        return "{}.wrap({}, ...)".format(__package__, formatted)


def raiser(exception=Exception, *args, **kwargs):
    """
    Create a callable that will immediately raise `exception` when called.

    Arguments, if any, will be passed along to the exception's constructor.
    """
    return ExceptionRaiser(exception, args, kwargs)


class ExceptionRaiser:
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
            return "exceptional.raiser({}, ...)".format(name)
        else:
            return "exceptional.raiser({})".format(name)
