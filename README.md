# WoLLM-HA-Client

Custom integration for Home Assistant that exposes a WoLLM server as a device with:

- model select
- wake, load, unload and shutdown buttons
- shutdown-on-idle switch
- status and RAM sensors
- service calls for automations

## Install with HACS

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository of type `Integration`.
3. Search for `WoLLM-HA-Client` and install it.
4. Restart Home Assistant.
5. Add the integration from `Settings -> Devices & Services`.

Repository URL for HACS custom repository:

```text
https://github.com/<your-account>/WoLLM-HA-Client
```

## Configuration

The config flow asks for:

- `Name`
- `Host or IP`
- `Port` (default `8080`)
- `MAC address`
- `API key` (optional)

The integration can be saved even if the WoLLM server is currently offline. If the API key is wrong and the server is reachable, setup is rejected with an authentication error.

## Entities

Each WoLLM config entry creates one Home Assistant device with:

- `select.model`
- `button.wake_server`
- `button.load_selected_model`
- `button.unload_model`
- `button.shutdown_server`
- `button.force_shutdown_server`
- `switch.shutdown_on_idle`
- `sensor.server_status`
- `sensor.current_model`
- `sensor.idle_seconds`
- `sensor.ram_used_mb`
- `sensor.ram_total_mb`
- `sensor.wol_boot`

## Services

The integration also registers these Home Assistant services under `wollm`:

- `wollm.wake`
- `wollm.load_model`
- `wollm.unload_model`
- `wollm.shutdown`
- `wollm.refresh_models`

When more than one WoLLM server is configured, pass `entry_id` to the service call.

## Notes

- Wake-on-LAN uses the configured MAC address and infers a broadcast target from the configured host when possible.
- If WoLLM is offline, API-backed entities become unavailable; the wake button stays available.
- Normal shutdown may fail if WoLLM requires `forceShutdown=true`. In that case use the dedicated force shutdown button or service field.
- GitHub Actions for `hacs` validation and `hassfest` are included to help keep the repository publishable.

## Versioning

This project follows Semantic Versioning.

- `0.1.0` is the initial public release
- patch releases (`0.1.1`) are for fixes
- minor releases (`0.2.0`) are for new backward-compatible features
- `1.0.0` will mark the first stable release
