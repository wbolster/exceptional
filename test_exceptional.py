import inspect

import exceptional
import pytest


def test_suppress_repr():
    x = exceptional.suppress(KeyError, IndexError)
    expected = "exceptional.suppress(KeyError, IndexError)"
    assert str(x) == repr(x) == expected


def test_suppress_context_manager():

    # One argument
    with exceptional.suppress(ValueError):
        raise ValueError

    # Multiple arguments
    with exceptional.suppress(ValueError, TypeError):
        raise TypeError

    # Make sure only the right exceptions are suppressed
    with pytest.raises(ValueError):
        with exceptional.suppress(TypeError):
            raise ValueError


def test_suppress_decorator():
    @exceptional.suppress(ValueError)
    def a():
        raise ValueError

    @exceptional.suppress(TypeError)
    def b():
        raise ValueError

    # Should not raise
    a()

    # Should raise
    with pytest.raises(ValueError):
        b()


def test_collector_context_manager():
    c = exceptional.collect(ValueError, TypeError)

    with c:
        pass

    with c:
        raise TypeError

    with pytest.raises(IOError):
        with c:
            # This exception should not be collected.
            raise IOError

    exceptions = list(c)
    assert len(exceptions) == 1
    assert type(exceptions[0]) == TypeError


def test_collector_repr():
    c = exceptional.collect(ValueError, TypeError)
    assert str(c) == repr(c) == "exceptional.collect(ValueError, TypeError)"


class CustomException(Exception):
    pass


class CustomExceptionTwo(Exception):
    pass


class CustomExceptionThree(Exception):
    pass


def test_wrap():
    with pytest.raises(CustomException):
        with exceptional.wrap(ValueError, CustomException):
            raise ValueError


def test_wrap_no_exception():
    with exceptional.wrap(ValueError, CustomException):
        pass


def test_wrap_not_handled():
    with pytest.raises(IndexError):
        with exceptional.wrap(ValueError, CustomException):
            raise IndexError


def test_wrap_multiple_exceptions():
    wrapper = exceptional.wrap((KeyError, IndexError), CustomException)

    with pytest.raises(CustomException), wrapper:
        raise KeyError

    with pytest.raises(CustomException), wrapper:
        raise IndexError


def test_wrap_multiple_exceptions_mapping():
    mapping = {
        KeyError: CustomException,
        LookupError: CustomExceptionTwo,
        (ValueError, TypeError): CustomExceptionThree,
    }
    wrapper = exceptional.wrap(mapping)

    with pytest.raises(CustomException), wrapper:
        raise KeyError

    with pytest.raises(CustomExceptionTwo), wrapper:
        assert issubclass(IndexError, LookupError)
        raise IndexError

    with pytest.raises(CustomExceptionThree), wrapper:
        raise ValueError

    with pytest.raises(CustomExceptionThree), wrapper:
        raise TypeError


def test_wrap_message_propagated_by_default():
    """
    By default, the exception message is propagated as-is.
    """
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException):
            raise ValueError("foo")
    assert str(exc_info.value) == "foo"


def test_wrap_message():
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, message="foo {}"):
            raise ValueError("bar")
    assert str(exc_info.value) == "foo {}"


def test_wrap_empty_message():
    """
    The replacement message can be empty.
    """
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, message=None):
            raise ValueError("foo")
    assert exc_info.value.args == ()
    assert str(exc_info.value) == ""


def test_wrap_message_prefix():
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, prefix="foo"):
            raise ValueError("bar")
    assert str(exc_info.value) == "foo: bar"

    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, prefix="{}"):
            raise ValueError("bar")
    assert str(exc_info.value) == "{}: bar"


def test_wrap_message_format():
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, format="oops ({})"):
            raise ValueError("foo")
    assert str(exc_info.value) == "oops (foo)"


def test_wrap_cause():
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException):
            raise ValueError("foo")
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == "foo"

    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, set_cause=False):
            raise ValueError("foo")
    assert exc_info.value.__cause__ is None


def test_wrap_context():
    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException):
            raise ValueError("foo")
    assert isinstance(exc_info.value.__context__, ValueError)
    assert str(exc_info.value.__context__) == "foo"

    with pytest.raises(CustomException) as exc_info:
        with exceptional.wrap(ValueError, CustomException, suppress_context=True):
            raise ValueError
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert isinstance(exc_info.value.__context__, ValueError)
    assert exc_info.value.__suppress_context__


def test_wrap_repr():
    x = exceptional.wrap(ValueError, CustomException)
    expected = "exceptional.wrap(ValueError, CustomException, ...)"
    assert str(x) == repr(x) == expected

    mapping = {}
    x = exceptional.wrap(mapping)
    expected = "exceptional.wrap({}, ...)"
    assert str(x) == repr(x) == expected

    mapping = {ValueError: CustomException, IndexError: CustomExceptionTwo}
    x = exceptional.wrap(mapping)
    expected = "exceptional.wrap({IndexError: CustomExceptionTwo, ...}, ...)"
    assert str(x) == repr(x) == expected


def test_wrap_decorator():
    @exceptional.wrap(ValueError, CustomException)
    def a():
        raise ValueError

    with pytest.raises(CustomException):
        a()


def test_wrap_invalid_usage():
    with pytest.raises(TypeError) as exc_info:
        exceptional.wrap({KeyError: CustomException}, CustomException)
    expected = "cannot specify both a mapping and a replacement exception type"
    assert str(exc_info.value) == expected

    with pytest.raises(TypeError) as exc_info:
        exceptional.wrap(KeyError, 123)
    assert str(exc_info.value) == "not an exception class: 123"

    with pytest.raises(TypeError) as exc_info:
        exceptional.wrap(123, CustomException)
    assert str(exc_info.value) == "not an exception class (or tuple): 123"

    with pytest.raises(TypeError) as exc_info:
        exceptional.wrap(ValueError, CustomException, message="foo", format="bar")
    expected = "specify at most one of 'message', 'prefix', or 'format'"
    assert str(exc_info.value) == expected


def test_raiser_no_args():
    f = exceptional.raiser()
    with pytest.raises(Exception):
        f()


def test_raiser_args():
    f = exceptional.raiser(ValueError, "abc")

    with pytest.raises(ValueError):
        f()

    try:
        f(123)
    except ValueError as exc:
        assert "abc" == str(exc)
    else:
        assert False, "did not raise"


def test_raiser_repr():
    r = exceptional.raiser(ValueError)
    assert str(r) == repr(r) == "exceptional.raiser(ValueError)"

    r = exceptional.raiser(ValueError, "some message")
    assert str(r) == repr(r) == "exceptional.raiser(ValueError, ...)"


def test_missing_arg_repr():
    """
    Test ``repr()`` for missing/default args.

    Used by Sphinx autodoc, and required for full test coverage.
    """
    argspec = inspect.getfullargspec(exceptional.wrap)
    assert repr(argspec.kwonlydefaults["message"]) == "<MISSING>"
