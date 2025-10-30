# Changelog

All notable changes to TestForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **GitHub Actions Integration** - Complete CI/CD workflows for automated testing
  - Main workflow: `api-integration-test.yml` - Full end-to-end test pipeline
  - Individual action workflows (5 separate workflows):
    - `action-1-download-example.yml` - Download example template
    - `action-2-combination.yml` - Generate test combinations
    - `action-3-compile.yml` - Compile to Robot Framework
    - `action-4-run-stream.yml` - Run tests with SSE streaming
    - `action-5-download-report.yml` - Download test reports
  - Auto-trigger on push to `master` branch (when `app/**` changes)
  - Auto-trigger on pull requests to `master`
  - Manual workflow dispatch with custom inputs
  - Comprehensive artifact uploads (30 days retention)
  - Health check and server startup validation
  - SSE stream output logging
  - Detailed troubleshooting documentation

### Changed
- Updated `README.md` with GitHub Actions integration section
- Added workflow badge to README
- Updated Table of Contents to include GitHub Actions

### Documentation
- Created `.github/workflows/README.md` - Comprehensive workflow documentation
- Created `GITHUB_ACTIONS_QUICKREF.md` - Quick reference card for common commands
- Added usage examples for all workflows
- Added troubleshooting guide for common issues

---

## [0.1.0] - 2025-10-30

### Added
- Initial release of TestForge
- FastAPI server with REST endpoints
- Test combination generator (pairwise/all-pairs)
- Robot Framework test compiler
- Real-time test execution with SSE streaming
- Test report download and packaging
- GitHub Actions trigger endpoint
- Docker support with docker-compose
- Comprehensive API documentation (Swagger/ReDoc)
- Example templates and documentation
- Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Request/response logging in test cases
- Sentinel keywords ([EMPTY], [NULL], etc.)
- Dynamic assertions with operators
- Type casting support
- Nested object and array handling

### Features
- ✅ CSV/XLSX input support
- ✅ Automatic base URL detection
- ✅ Smart path normalization
- ✅ Comprehensive prefix system
- ✅ Operator-based assertions
- ✅ SSE streaming for real-time updates
- ✅ Zip-compressed reports
- ✅ Health check endpoints

---

[Unreleased]: https://github.com/Baipo-Production/test-forge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Baipo-Production/test-forge/releases/tag/v0.1.0
