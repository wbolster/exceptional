===========
exceptional
===========

.. py:currentmodule:: exceptional

``exceptional`` is a small Python library providing various exception
handling utilities.


.. contents::
   :local:
   :depth: 2
   :backlinks: none


Installation
============

::

  pip install exceptional

``exceptional`` supports reasonably modern Python versions, which at
the time of writing means Python 3.4+.

Usage and API
=============

All functionality is available from the ``exceptional`` module::

  import exceptional

Suppressing exceptions
----------------------

The :py:func:`exceptional.suppress` function can be used as a context
manager as a succinct way to suppress one or more exceptions::

    with exceptional.suppress(FileNotFoundError):
        os.remove(...)

This is similar to simply ignoring exceptions like this, but shorter::

    try:
        os.remove(...)
    except FileNotFoundError:
      pass

This behaves the same as the ``contextlib.suppress()`` from the
standard library, but this implementation can also be used as a
decorator::

    @exceptional.suppress(ValueError, LookupError):
    def do_something():
        ...

.. autofunction:: exceptional.suppress


Collecting exceptions
---------------------

The :py:func:`exceptional.collect` function can be used to collect exceptions.
This is similar to :py:func:`exceptional.suppress`, but remembers the raised
exceptions::

    collector = exceptional.collect(ValueError, TypeError)
    for item in ...:
        with collector:
          do_something(item)

To access the collected exceptions, iterate over the collector::

    for exc in collector:
        print(exc)

Note that :py:func:`exceptional.collect` cannot be used as a
decorator, since there is no sensible way to obtain the results, and
it could result in an ever-growing list of collected exceptions which
cannot be cleared.

.. autofunction:: exceptional.collect


Creating exception-raising callables
------------------------------------

The :py:func:`exceptional.raiser` function can be used to quickly
create a callable that raises an exception when called. This can be
useful to create callback functions that should do nothing besides
immediately raise an exception::

    callback = raiser(RuntimeError, "that took way too long")

Any arguments passed to this function, such as the error message
above, will be passed along to the exception's constructor.
The returned callable can now be used in callback-based APIs, for
example with an ``asyncio`` event loop:

::

    loop = ...
    loop.call_later(delay, callback)
    loop.run_forever()

The above cannot be done using a ``lambda`` expression, since
``raise`` is a statement, and statements cannot be used inside
``lambda`` expressions.

The callable returned by :py:func:`exceptional.raiser` will accept any
arguments and ignore those, making them suitable for use as a
callback, regardless of the expected signature.

.. autofunction:: exceptional.raiser


Contributing
============

The source code and issue tracker for this package can be found on Github:

  https://github.com/wbolster/exceptional


.. include:: ../LICENSE.rst
