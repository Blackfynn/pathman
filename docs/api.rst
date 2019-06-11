.. _api:
.. _docs: https://s3fs.readthedocs.io/en/latest/

===
API
===

Path
====

.. autoclass:: pathman.AbstractPath
   :members:

.. class:: pathman.S3Path

    A wrapper around `s3fs.S3FileSystem`. All S3 paths should
    begin with ``s3://``. See the s3fs docs_ for additional
    initialization arguments.

    .. data:: bucket

        Returns the s3 bucket for this path

        Return type
            ``str``

    .. data:: key

        Returns the path for this object without the bucket

        Return type
            ``List[str]``


.. class:: pathman.BlackfynnPath

    An interface for intereracting with the Blackfynn platform as
    a filesystem.

    .. method:: __init__(path, dataset=None, profile='default', **kwargs)

        parameters
            **path** (*str*) – The path to a file or folder on the Blackfynn
            platform, which must begin with ``bf://``. The dataset is optional
            as a first component of the path.

            **dataset** (*str, optional*) – If this argument is ``None``, then the dataset name will
            be inferred from the first component of ``path``.

            **profile** (*str, optional*) – The profile to use when interacting with the Blackfynn API.
            If no value is provided, the ``default`` profile will be used.

    .. data:: dataset

        Returns the name of this path's dataset on the platform

        Return type
            ``str``

    .. method:: open

        Raises a ``NotImplementedError`` because it isn't possible
        to open files on the Blacfynn platform.

    .. note::
        Objects on the Blackfynn platform do not have extensions
        natively, and so BlackfynnPath does its best to infer the
        extension of objects on the platform by using the extension
        of an object's first source file. For objects with multiple
        source files, this will cause a warning to be logged.

    .. warning::

         - The ``write_bytes`` and ``write_text`` operations do not support
           the append mode. Any existing data will be overwritten by these
           operations.
         - The ``read_bytes`` and ``read_text`` methods will only read
           the contents of the first source file.

.. autofunction:: pathman.path.copy

.. autofunction:: pathman.utils.is_file

Exceptions
==========

.. automodule:: pathman.exc
   :members:
