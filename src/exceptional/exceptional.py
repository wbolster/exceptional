import collections
import contextlib
import inspect
import operator
import types
import typing


def escape_format_string(s: str) -> str:
    return s.replace("{", "{{").replace("}", "}}")


def is_exception_class(x: typing.Any) -> bool:
    return inspect.isclass(x) and issubclass(x, BaseException)


def is_multiple_exception_classes(x: typing.Any) -> bool:
    return isinstance(x, collections.abc.Sequence) and all(
        is_exception_class(item) for item in x
    )


class Missing:
    def __repr__(self) -> str:
        return "<MISSING>"


MISSING = Missing()

MissingOrMaybeString = typing.Union[Missing, typing.Optional[str]]
UnnormalizedExceptionMapping = typing.Mapping[
    typing.Union[
        typing.Type[BaseException], typing.Sequence[typing.Type[BaseException]]
    ],
    typing.Type[BaseException],
]
ExceptionMapping = typing.Mapping[
    typing.Type[BaseException], typing.Type[BaseException]
]


def suppress(*exceptions: typing.Type[BaseException]) -> "ExceptionSuppressor":
    """
    Suppress the specified exception(s).

    This can be used as a context manager or as a decorator.
    """
    return ExceptionSuppressor(*exceptions)


class ExceptionSuppressor(contextlib.ContextDecorator):
    def __init__(self, *exceptions: typing.Type[BaseException]) -> None:
        self._exceptions = exceptions

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: typing.Optional[types.TracebackType],
    ) -> bool:
        return exc_type is not None and issubclass(exc_type, self._exceptions)

    def __repr__(self) -> str:
        formatted = ", ".join(exc.__qualname__ for exc in self._exceptions)
        return "{}.suppress({})".format(__package__, formatted)


def collect(*exceptions: typing.Type[BaseException]) -> "ExceptionCollector":
    """
    Create a collector for the specified exception(s).

    This can be used as a context manager. Iterate over the returned collector
    object to access the collected exceptions.
    """
    return ExceptionCollector(*exceptions)


class ExceptionCollector:
    """
    Exception collection helper; see ``collect()``.
    """

    def __init__(self, *exceptions: typing.Type[BaseException]):
        self._exceptions = exceptions
        self._collected_exceptions: typing.MutableSequence[BaseException] = []

    def __enter__(self) -> "ExceptionCollector":
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: typing.Optional[types.TracebackType],
    ) -> bool:
        if exc_type is None:
            return True
        elif issubclass(exc_type, self._exceptions) and exc_value is not None:
            self._collected_exceptions.append(exc_value)
            return True
        else:
            return False

    def __repr__(self) -> str:
        formatted = ", ".join(exc.__qualname__ for exc in self._exceptions)
        return "{}.collect({})".format(__package__, formatted)

    def __iter__(self) -> typing.Iterator[BaseException]:
        yield from self._collected_exceptions


@typing.overload
def wrap(
    original_or_mapping: typing.Type[BaseException],
    replacement: typing.Type[BaseException],
    *,
    message: MissingOrMaybeString = MISSING,
    prefix: typing.Optional[str] = None,
    format: typing.Optional[str] = None,
    set_cause: bool = True,
    suppress_context: bool = False
) -> "ExceptionWrapper":
    ...  # pragma: no cover


@typing.overload  # noqa: F811
def wrap(
    original_or_mapping: UnnormalizedExceptionMapping,
    *,
    message: MissingOrMaybeString = MISSING,
    prefix: typing.Optional[str] = None,
    format: typing.Optional[str] = None,
    set_cause: bool = True,
    suppress_context: bool = False
) -> "ExceptionWrapper":
    ...  # pragma: no cover


def wrap(  # noqa: F811
    original_or_mapping: typing.Union[
        UnnormalizedExceptionMapping, typing.Type[BaseException]
    ],
    replacement: typing.Optional[typing.Type[BaseException]] = None,
    *,
    message: MissingOrMaybeString = MISSING,
    prefix: typing.Optional[str] = None,
    format: typing.Optional[str] = None,
    set_cause: bool = True,
    suppress_context: bool = False
) -> "ExceptionWrapper":
    """
    Raise a replacement exception wrapping the original exception.

    This can be used as a context manager or as a decorator.
    """
    items: typing.Iterable[
        typing.Tuple[
            typing.Union[
                typing.Type[BaseException], typing.Sequence[typing.Type[BaseException]]
            ],
            typing.Optional[typing.Type[BaseException]],
        ]
    ]
    if isinstance(original_or_mapping, collections.abc.Mapping):
        if replacement is not None:
            raise TypeError(
                "cannot specify both a mapping and a replacement exception type"
            )
        items = original_or_mapping.items()
    else:
        items = [(original_or_mapping, replacement)]

    mapping: ExceptionMapping = {}
    for original, replacement in items:
        if not is_exception_class(replacement):
            raise TypeError("not an exception class: {!r}".format(replacement))
        if is_exception_class(original):
            mapping[original] = replacement  # type: ignore
        elif is_multiple_exception_classes(original):
            for exc in original:  # type: ignore
                mapping[exc] = replacement  # type: ignore
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
    elif isinstance(message, str):
        format = escape_format_string(message)

    return ExceptionWrapper(
        mapping=mapping,
        format=format,
        set_cause=set_cause,
        suppress_context=suppress_context,
    )


class ExceptionWrapper(contextlib.ContextDecorator):
    """
    Exception wrapping helper; see ``wrap()``.
    """

    def __init__(
        self,
        *,
        mapping: ExceptionMapping,
        format: typing.Optional[str],
        set_cause: bool,
        suppress_context: bool
    ):
        self._mapping = mapping
        self._format = format
        self._set_cause = set_cause
        self._suppress_context = suppress_context

    def __enter__(self) -> "ExceptionWrapper":
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: typing.Optional[types.TracebackType],
    ) -> bool:
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
                # https://github.com/python/typeshed/issues/2875
                exc.__suppress_context__ = True  # type: ignore
            raise exc

        return False  # Cannot be handled here.

    def _find_replacement_exception_class(
        self, exception_class: typing.Type[BaseException]
    ) -> typing.Optional[typing.Type[BaseException]]:
        for cls in exception_class.mro():
            try:
                return self._mapping[cls]
            except KeyError:
                pass
        else:
            return None

    def __repr__(self) -> str:
        if not self._mapping:
            formatted = "{}"
        elif len(self._mapping) == 1:
            original, new = next(iter(self._mapping.items()))
            formatted = "{}, {}".format(original.__qualname__, new.__qualname__)
        else:
            get_name = operator.attrgetter("__qualname__")
            original = min(self._mapping.keys(), key=get_name)
            new = self._mapping[original]
            formatted = "{{{}: {}, ...}}".format(
                original.__qualname__, new.__qualname__
            )

        return "{}.wrap({}, ...)".format(__package__, formatted)


def raiser(
    exception: typing.Type[BaseException] = Exception,
    *args: typing.Any,
    **kwargs: typing.Any
) -> "ExceptionRaiser":
    """
    Create a callable that will immediately raise `exception` when called.

    Arguments, if any, will be passed along to the exception's constructor.
    """
    return ExceptionRaiser(exception, args, kwargs)


class ExceptionRaiser:
    """
    Exception raising helper; see ``raiser()``.
    """

    def __init__(
        self,
        exception_class: typing.Type[BaseException],
        exception_args: typing.Sequence[typing.Any],
        exception_kwargs: typing.Mapping[str, typing.Any],
    ):
        self.exception_class = exception_class
        self.exception_args = exception_args
        self.exception_kwargs = exception_kwargs

    def __call__(self, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        exc = self.exception_class(  # type: ignore
            *self.exception_args, **self.exception_kwargs
        )
        raise exc

    def __repr__(self) -> str:
        name = self.exception_class.__qualname__
        if self.exception_args or self.exception_kwargs:
            return "exceptional.raiser({}, ...)".format(name)
        else:
            return "exceptional.raiser({})".format(name)
