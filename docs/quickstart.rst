.. _quickstart:

==========
Quickstart
==========

Reading/Writing
---------------

Start by creating a new empty file to play with::

   >>> from pathman import Path
   >>> p = Path("~/Desktop/hello_world.txt")
   >>> p = p.expanduser()
   >>> p.exists()
   False
   >>> p.touch()
   >>> p.exists()
   True

We can write some text to it::

   >>> p.read_text()
   ''
   >>> p.write_text("Hello World!")
   12

and now read that text back::

   >>> p.read_text()
   'Hello World!'

We can use an identical interface for a file stored on S3::

   >>> s3_file = Path("s3://test-bucket/hello_world.txt")
   >>> s3_file.exists()
   False
   >>> s3_file.touch()
   >>> s3_file.exists()
   True
   >>> s3_file.read_text()
   ''
   >>> s3_file.write_text("Hello world!")
   12
   >>> s3_file.read_text()
   'Hello world!'

Moving Files
------------

Using the `copy` function, we can move data  between the supported data stores::

   >>> from pathman.copy import copy
   >>> local_file = Path("~/Desktop/local.txt").expanduser()
   >>> local_file.touch()
   >>> local_file.write_text("I'm a local file")
   >>> remote_dest = Path("s3://test-bucket/")
   >>> copy(local_file, remote_dest)
   >>> remote_file = remote_dest / "local.txt"
   >>> remote_file.exists()
   True
   >>> remote_file.read_text()
   'I'm a local file'

You can also pass s3-specific arguments to copy. For example, you can copy the file to s3 using SSE::

   >>> copy(local_file, remote_dest, SSEKMSKeyId="secret", ServerSideEncryption="aws:kms"))

This is just the begining! To see more of what you can do, check out the :ref:`api` documentation.
