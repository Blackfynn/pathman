# Pathman

Pathman is a utility for interacting with files using a uniform interface regardless of where
the files live: locally, on S3, or in some other remote service. It borrows heavily from the
design of the `pathlib` interface, but extends it to work with remote files.

The library currently supports interacting with local files and files stored on S3. Support for S3
files is done through heavy use of the `s3fs` library.



## Testing
Tests can be run with 

```bash
make test
```

## Basic Useage

```python
from pathman.path

```

