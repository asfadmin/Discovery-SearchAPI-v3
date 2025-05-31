# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/) 
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


<!--
## Example template!!

## [version](https://github.com/asfadmin/Discovery-PytestAutomation/compare/vOLD...vNEW)

### Added:
-

### Changed:
-

### Fixed:
- 

### Removed:
-

-->
------
## [1.0.2](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.1...v1.0.2)

### Fixed
- Omit `session` in `python` output

### Changed
- bump asf-search to 8.3.4 for latest `NISAR` collections

------
## [1.0.1](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.0...v1.0.1)

### Fixed
- Generic searches (non-search related params) no longer accepted, raise 400
- Fixed string comparison of numbers in range filters

### Changed
- Include wkt in error when raising in `validate_wkt()`
- Specify which binary file types are allowed to be passed to lambda

### Added
- Add dedicated dev branch for test-staging deployment
   - Intended Dev->Release workflow
      - dev -> test -> prod-staging -> prod
- Added more files to integration testing endpoint
- Add remaining file upload support for .zip and .shp files. All previous file formats now supported 

### Changed
- pin `asf-search` to v8.3.3, All basic Vertex dataset searches working

## [1.0.0](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v0.1.0...v1.0.0)

### Added
- SearchAPI-V3 basic feature parity with SearchAPI-V2
- Add `python` output type, generates equivalent asf-search code for results

### Tests
- Added non-edc deployments, tweaked CDK definition to accommodate
- Added non-edc staging deployments, (test -> prod-staging -> prod)
- legacy pytest suite tests working, using FastAPI TestClient
- Adds integration tests for merges to test and prod-staging


------
## [0.1.0](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v0.0.1...v0.1.0)

### Added
- Legacy API V2 Pytest suite Added, all tests passing

------

## [0.0.1](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v0.0.0...v0.0.1)

### Added
- Changelog
- Semantic Versioning
- Github Releases
------
