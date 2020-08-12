# Changelog

All notable changes to this project will be documented in this file

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.2.1]
### Changed
- Removed optional requirements from requirements.txt

### Fixed
- Include `pathman._impl` in build. 0.2.0 was a broken release.

## [0.2.0]
### Changed
- Only import optional dependencies (s3fs, boto3) when needed

### Removed
- Removed BlackfynnPath, which has gone unused

## [0.1.5]
### Added
- Parallelism on s3 -> local copies

### Fixed
- Recursive copies would create too many directories

## [0.1.4]
### Added
- A new function (`copy_s3_local`) to copy from s3 to local

## [0.1.3]
### Added
- Path.walk() now takes `**kwargs` to pass into the underlying implementation

### Fixed
- S3Path.walk() was returning a generator of tuples in the style of
  os.walk(), it has been changed to return a generator of S3Paths
  instead

### Changed
- All walk() implementations return generators instead of lists

## [0.1.1]
- Initial release
