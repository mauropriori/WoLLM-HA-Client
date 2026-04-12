# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and the project follows Semantic Versioning.

## [0.1.0] - 2026-04-12

### Added

- Initial HACS-ready Home Assistant custom integration for WoLLM.
- Config flow with host, port, MAC address and optional API key.
- Buttons for wake, load selected model, unload, shutdown and force shutdown.
- Model select entity and shutdown-on-idle switch.
- Sensors for server status, current model, idle time, RAM usage and WoL boot.
- Home Assistant services for wake, load, unload, shutdown and model refresh.
- Diagnostics support, README, `.gitignore`, and GitHub Actions for `hacs` and `hassfest`.
