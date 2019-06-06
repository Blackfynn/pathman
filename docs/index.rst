.. _Blackfynn: http://www.blackfynn.com/
.. _Graph-Ingest: https://github.com/Blackfynn/graph-ingest/
.. _s3fs: https://s3fs.readthedocs.io/en/latest/
.. _pathlib: https://docs.python.org/3/library/pathlib.html

Pathman
=======

Pathman is a utility for interacting with files using a uniform interface
regardless of where the files live: locally, on S3, or in some other remote
service. The interface attempts to follow the design of the `pathlib`
interface when possible. Support for interacting with files in S3 is
done through heavy use of the s3fs_ library. Support for paths on the
Blackfynn_ platform is made possible by the python client

Libraries Using Pathman
=======================
Graph-Ingest_


Next Steps
==========
.. toctree::
   :maxdepth: 2

   installation
   quickstart
   api
   dev
