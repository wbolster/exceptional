import exceptional
import pytest


def test_suppress_repr():
    x = exceptional.suppress(KeyError, IndexError)
    expected = "suppress(KeyError, IndexError)"
    assert str(x) == repr(x) == expected


def test_suppress_context_manager():

    # One argument
    with exceptional.suppress(ValueError):
        raise ValueError()

    # Multiple arguments
    with exceptional.suppress(ValueError, TypeError):
        raise TypeError()

    # Make sure only the right exceptions are suppressed
    with pytest.raises(ValueError):
        with exceptional.suppress(TypeError):
            raise ValueError()


def test_suppress_decorator():
    @exceptional.suppress(ValueError)
    def a():
        raise ValueError()

    @exceptional.suppress(TypeError)
    def b():
        raise ValueError()

    # Should not raise
    a()

    # Should raise
    with pytest.raises(ValueError):
        b()


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
    assert str(r) == repr(r) == "raiser(ValueError)"

    r = exceptional.raiser(ValueError, "some message")
    assert str(r) == repr(r) == "raiser(ValueError, ...)"


def test_collector():
    c = exceptional.collect(ValueError, TypeError)

    # Run some functions.
    c.run(int, 4)
    c.run(int, "abc")  # raises ValueError
    c.run(int, None)  # raises TypeError
    c.run(int, 5)

    # Context manager should behave the same as .run()
    with c:
        raise TypeError()

    # This exception should not be collected.
    with pytest.raises(IOError):
        with c:
            raise IOError()

    # Collector has collected results
    assert len(list(c)) == 5
    for rv, exc in c:
        if rv is not None:
            assert exc is None

    # Collector has collected return values
    assert list(c.iter_results()) == [4, 5]

    # Collector has collected exceptions
    exceptions = list(c.iter_exceptions())
    assert len(exceptions) == 3
    assert isinstance(exceptions[0], ValueError)
    assert isinstance(exceptions[1], TypeError)
    assert isinstance(exceptions[2], TypeError)


def test_collector_repr():
    c = exceptional.collect(ValueError, TypeError)
    assert str(c) == repr(c) == "collect(ValueError, TypeError)"
