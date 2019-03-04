# Pathman

Pathman is a utility for interacting with files using a uniform interface regardless of where
the files live: locally, on S3, or in some other remote service. Some have referred to it as the 
little utility library that gobbles of files regardless of where they are in the maze of our
modern world. 

The interface attempts to follow the design of the `pathlib` interface when possible. Support
for interacting with files in S3 is done through heavy use of the [s3fs](https://s3fs.readthedocs.io/en/latest/) 
library.

## Testing
Tests can be run with 

```bash
make test
```

## Projects Using the Library
- [Graph Ingest](https://github.com/Blackfynn/graph-ingest/)

