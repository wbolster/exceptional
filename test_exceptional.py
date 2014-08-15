
import exceptional
import pytest


def test_suppress():

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


def test_collector():
    c = exceptional.Collector(ValueError, TypeError)

    assert 4 == c.run(int, 4)  # works fine
    c.run(int, 'abc')  # raises ValueError
    c.run(int, object())  # raises TypeError
    assert 5 == c.run(int, 5)  # also works fine

    assert len(c.exceptions) == 2
    assert isinstance(c.exceptions[0], ValueError)
    assert isinstance(c.exceptions[1], TypeError)
