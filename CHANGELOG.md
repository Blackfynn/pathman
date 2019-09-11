# Changelog

All notable changes to this project will be documented in this file

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.1.2]
### Added
- Path.walk() now takes `**kwargs` to pass into the underlying implementation

### Fixed
- S3Path.walk() was returning a generator in the style of os.walk(),
  it has been changed to return a list of S3Paths instead

### Changed
- All walk() now return generators instead of lists

## [0.1.1]
- Initial release
