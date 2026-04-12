# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and the project follows Semantic Versioning.

## [0.1.2] - 2026-04-12

### Fixed

- Prepared a tagged patch release so HACS can resolve the update from a semantic version instead of commit hashes.

## [0.1.1] - 2026-04-12

### Fixed

- Updated GitHub Actions workflows to use `actions/checkout@v5`.
- Corrected the HACS validation workflow ignore list format for repository metadata checks.
- Added local brand assets required by HACS under `custom_components/wollm/brand/`.

## [0.1.0] - 2026-04-12

### Added

- Initial HACS-ready Home Assistant custom integration for WoLLM.
- Config flow with host, port, MAC address and optional API key.
- Buttons for wake, load selected model, unload, shutdown and force shutdown.
- Model select entity and shutdown-on-idle switch.
- Sensors for server status, current model, idle time, RAM usage and WoL boot.
- Home Assistant services for wake, load, unload, shutdown and model refresh.
- Diagnostics support, README, `.gitignore`, and GitHub Actions for `hacs` and `hassfest`.
