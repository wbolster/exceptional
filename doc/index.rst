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

Usage
=====

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

Wrapping exceptions
-------------------

The :py:func:`exceptional.wrap` function can be used to catch an
exception (or multiple exceptions), and raise a replacement exception
in its place. This should be used with care, but can be useful to to
(partially) hide exceptions from underlying libraries by converting
them to application-specific exceptions.

By default, the original exception is set as the direct cause of the
new exception, using a mechanism that is equivalent to a statement of
the form::

    raise NewException(...) from original

In practice, this means that the Python interpreter will show both
exceptions (including tracebacks) when the exception causes the
application to crash. For more information, see the Python
documentation about `exceptions
<https://docs.python.org/3/library/exceptions.html>`_ and the `raise
statement
<https://docs.python.org/3/reference/simple_stmts.html#raise>`_.


The examples below show basic usage.

* A context manager can be a convenient replacement for a longer
  ``try``/``except``/``raise from`` combination::

      class ConfigurationError(Exception):
          pass

      def load_configuration(config_file):
          with exceptional.wrap(FileNotFoundError, ConfigurationError)
              with open(config_file, 'r') as fp:
                  return json.load(fp)

* A decorator achieves similar behaviour for a complete function::

      @exceptional.wrap(FileNotFoundError, ConfigurationError)
      def load_configuration(config_file):
          with open(config_file, 'r') as fp:
              return json.load(fp)

The above examples replace a single exception with another one.
Handling multiple exceptions can be done in two ways:

* provide a tuple, just like a regular ``except`` statement::

      with exceptional.wrap((ValueError, KeyError), CustomException):
          ...

* provide a mapping, which allows for more complex configuration, and
  also correctly handles exception hierarchies::

      mapping = {
          ValueError: CustomException,
          KeyError: AnotherCustomException,
      }
      with exceptional.wrap(mapping):
          ...

By default the message for the first exception is reused for the
replacement exception. For more control over the message, use one of
the following (keyword-only) arguments.

* To provide a new message, use the `message` argument::

      with exceptional.wrap(ValueError, CustomException, message="oops"):
          ...

* Pass ``None`` to remove the message altogether::

      with exceptional.wrap(ValueError, CustomException, message=None):
          ...

* To add another message in front of the original message, use
  `prefix`::

      with exceptional.wrap(ValueError, CustomException, prefix="oops"):
          raise ValueError("foo")

  The above example results in ``CustomException("oops: foo")``.

* For more flexibility, use `format` and use a ``{}`` placeholder::

      template = "Something went wrong. Likely reason: {}. Please file a bug."
      with exceptional.wrap(ValueError, CustomException, format=template):
          ...

Finally, for more control over the exception *context* and *cause*,
use the `set_cause` and `suppress_context` args::

    with exceptional.wrap(ValueError, CustomException, set_cause=False):
        ...

    with exceptional.wrap(ValueError, CustomException, suppress_context=True):
        ...

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


API
===

.. autofunction:: exceptional.suppress
.. autofunction:: exceptional.collect
.. autofunction:: exceptional.wrap
.. autofunction:: exceptional.raiser

Contributing
============

The source code and issue tracker for this package can be found on Github:

  https://github.com/wbolster/exceptional


.. include:: ../LICENSE.rst
