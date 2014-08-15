
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
