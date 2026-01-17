# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- JSON parsing error in `decrypt_local_credentials()` for robot vacuum devices with `lecAndWifi` connectivity
  - Robot vacuums (e.g., Dyson 360 Vis Nav™, product_type "277") now properly decrypt local MQTT credentials
  - Fixed "Extra data" JSON parsing error at character position 145
  - Method now uses `JSONDecoder.raw_decode()` to handle multiple JSON objects or extra metadata in decrypted credentials
  - Added comprehensive test coverage for robot vacuum credential scenarios
  - Enhanced debug logging to output full decrypted credentials on parsing failures for troubleshooting

## [0.2.0] - 2025-08-17

### Added
- Complete OpenAPI-compliant implementation of Dyson App API v0.0.2-unstable
- AES-256-CBC decryption for MQTT local credentials using cryptography library
- Token-based authentication with bearer token storage and reuse
- Comprehensive data models for authentication, devices, and IoT operations
- MQTT client wrapper for device communication
- Support for both cloud and local MQTT connections
- Professional PyPI packaging with proper metadata and dependencies
- GitHub Actions workflow for automated publishing
- Comprehensive documentation and examples

### Changed
- Complete rewrite of API client to match official Dyson endpoints
- Improved error handling with custom exception classes
- Updated authentication flow to use proper two-step OTP process

### Fixed
- MQTT password decryption using correct AES algorithm
- Bearer token handling for API authentication
- Package structure following Python best practices

### Security
- Secure handling of authentication tokens and credentials
- Proper AES encryption/decryption implementation

## [0.1.0] - Previous Version
- Initial basic implementation (legacy)

[Unreleased]: https://github.com/cmgrayb/libdyson-rest/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/cmgrayb/libdyson-rest/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cmgrayb/libdyson-rest/releases/tag/v0.1.0
