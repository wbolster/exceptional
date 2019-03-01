import exceptional
import pytest


def test_suppress_repr():
    x = exceptional.suppress(KeyError, IndexError)
    expected = "suppress(KeyError, IndexError)"
    assert str(x) == expected
    assert repr(x) == expected


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


def test_collector():
    c = exceptional.Collector(ValueError, TypeError)

    # This should work fine
    assert 4 == c.run(int, 4)

    # These calls raise ValueError and TypeError
    c.run(int, "abc")
    c.run(int, object())

    # It should keep working...
    assert 5 == c.run(int, 5)

    # Context manager should behave the same as .run()
    with c:
        raise TypeError()

    with pytest.raises(IOError):
        with c:
            raise IOError()

    assert len(c.exceptions) == 3
    assert isinstance(c.exceptions[0], ValueError)
    assert isinstance(c.exceptions[1], TypeError)
    assert isinstance(c.exceptions[2], TypeError)
