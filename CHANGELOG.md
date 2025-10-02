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
## [1.0.8](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.7...v1.0.8)
### Changed
- bump asf-search to v10.1.0 for NISAR product type file sizes, urgent response now searchable with product types, and ARIA-S1 GUNW Stacking support, better nisar metadata output formatting

### Fixed
- boolean values are properly capitalized in `python` output file
- API maturity set for each level of deployment stage
- API maturity loaded once per api instance

------
## [1.0.7](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.6...v1.0.7)
### Changed
- bump asf-search to v9.0.8

------
## [1.0.6](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.5...v1.0.6)
### Changed
- bump asf-search to v9.0.7

------
## [1.0.5](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.4...v1.0.5)
### Added
- Added `json` output format support

### Changed
- bump asf-search to v9.0.6

------
## [1.0.5](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.4...v1.0.5)
### Added
- Create wrapper class around asf-search `ASFSession`, `SearchAPISession`. Modifies client ID.

### Changed
- Aria stack supports different output types
- Aria stacking uses aria frame id instead of frame number for stacking
- asf_search uses `SearchAPISession` by default for search queries
- bump asf-search to v9.0.4
- increase search query limit to 2000, raise error if expected output is over that number

------
## [1.0.4](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.3...v1.0.4)
### Added
- Added experimental ARIA S1 GUNW baseline stacking support
    - requires: `dataset` keyword be set to "ARIA S1 GUNW" and using the desired frame as the `reference`
    - returns json object list partially formatted for submitting jobs to ASF's On Demand processing.
        ``` json
        [
            {
                "date": "2025-06-04T00:26:25Z",
                "products": [
                "S1A_IW_SLC__1SDV_20250604T002649_20250604T002716_059489_076290_7E0F",
                "S1A_IW_SLC__1SDV_20250604T002625_20250604T002651_059489_076290_7FE0"
                ],
                "group_granule_idx": 0,
                "perpendicularBaseline": 0,
                "temporalBaseline": 0
            },
            {
                "date": "2025-05-23T00:26:25Z",
                "products": [
                "S1A_IW_SLC__1SDV_20250523T002650_20250523T002717_059314_075C80_5A5D",
                "S1A_IW_SLC__1SDV_20250523T002625_20250523T002652_059314_075C80_BBE7"
                ],
                "group_granule_idx": 0,
                "perpendicularBaseline": 47,
                "temporalBaseline": -12
            },

            ...
            
            {
                "date": "2014-10-12T00:25:42Z",
                "products": [
                "S1A_IW_SLC__1SSV_20141012T002607_20141012T002634_002789_00323B_2DB9",
                "S1A_IW_SLC__1SSV_20141012T002542_20141012T002609_002789_00323B_0E9F"
                ],
                "group_granule_idx": 0,
                "perpendicularBaseline": -160,
                "temporalBaseline": -3888
            }
        ]
        ```
### Changed
- bumped asf-search to 9.0.2 for nisar search types, browse images, and UAT collections, `productionConfiguration` list support, bbox validation, opera-disp jsonlite outputs


------
## [1.0.3](https://github.com/asfadmin/Discovery-SearchAPI-v3/compare/v1.0.2...v1.0.3)
### Changed
- Swap deployment region from us-west-2 to us-east-1

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
