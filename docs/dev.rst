.. _dev:
.. _pathlib: https://docs.python.org/3/library/pathlib.html
.. _os.path: https://docs.python.org/2/library/os.path.html

============
Developement
============


Testing
-------

Installation
~~~~~~~~~~~~

.. code-block:: bash

    pip install -r requirements-test.txt

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

    pytest

Integration tests::

    pytest --integration

Adding new Path implementations
-------------------------------

The pathman library comes packaged with several different path implementations,
but the user might want to create a filesystem interface for some application
specific to them.

Pathman's path interface is easily extensible, and new implementations can be
automatically added to ``Path``'s prefix-implementation mapping.

A New Class
~~~~~~~~~~~
All new path classes should inherit from ``AbstractPath``, and if your target
is in some remote location, should inherit ``RemotePath`` as well.

All classes which inherit from ``AbstractPath`` have the option of implementing
a ``prefix`` property, which will flag them to be automatically added to
``Path``'s implementation mapping. For example, all S3 paths start with
``s3://``, and so ``S3Path.prefix`` is ``s3``. Then, when you create a path (as
below), ``Path`` will know to initialize a ``S3Path`` object to match.

.. code-block:: python

    Path('s3://example-bucket/my-file')

The Constructor
~~~~~~~~~~~~~~~
The first argument to a Path object will always be a string which represents
the path for this object (eg. ``/Users/username/Desktop/file.txt``). This
argument, or some other string which best represents this path is then stored
in a variable called ``self._pathstr``. The constructor can (and probably will)
also recieve other information, like credentials for connecting to some remote
service represented by your path.

Methods and Properties
~~~~~~~~~~~~~~~~~~~~~~

AbstractPath requires the implementaion of many methods and properties, which
are all listed in ``abstract.py`` In general pathman seeks to conform to the
behavior of the built-in python modules pathlib_ and os.path_.

Not all methods are exactly mirrored by those libraries. Methods and properties
with differences are documented below.

* **extension** is equivalent to ``patlib.suffix``.
* **walk**: ``os.path.walk`` is depreciated in favor os ``os.walk``. This
  method returns a list of all files located in the directory specified by this
  path and all of its child directories. Symlinked directories are ignored.
* **ls** is equivalent to ``patlib.iterdir``.
* **remove** is equivalent to ``patlib.unlink`` and ``os.remove``.

In addition to these methods, AbstractPath implements ``__str__``,
``__repr__``, ``__eq__``, and ``__truediv__``. The division override
defined by Path objects takes a Path and a string, and returns a new Path
with the string appended to the original path. For example::

    >>> Path('~/Desktop') / 'file.txt'
    Path('~/Desktop/file.txt')

Paths may also implement non-required methods which provide additional
funcitonality based on the target platform. Some methods implemented by
``AbstractPath`` may not apply to your Path. In that case, raise a
``NotImplementedError``, or some other exception as appropriate in those
methods.
