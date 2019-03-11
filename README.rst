.. image:: https://codecov.io/gh/Blackfynn/pathman/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/Blackfynn/pathman
.. image:: https://travis-ci.org/Blackfynn/pathman.svg?branch=master
    :target: https://travis-ci.org/Blackfynn/pathman

.. _Blackfynn: http://www.blackfynn.com/
.. _Graph-Ingest: https://github.com/Blackfynn/graph-ingest/
.. _s3fs: https://s3fs.readthedocs.io/en/latest/

=======
Pathman
=======

Pathman is a utility for interacting with files using a uniform interface regardless of where
the files live: locally, on S3, or in some other remote service. The interface attempts closely
follow the `pathlib` interface when possible. Support for interacting with files in S3 is done 
through heavy use of the s3fs_ library.
