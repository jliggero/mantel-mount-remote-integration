# MantelMount Remote Integration

A Home Assistant integration to control your MantelMount lift system via UDP commands.

## Installation

1. In HACS, go to **Integrations** and add `https://github.com/jliggero/mantel-mount-remote-integration` as a custom repository (type: Integration).
2. Install the `MantelMount Remote` integration.
3. Restart Home Assistant (`ha core restart`).
4. Go to **Settings > Devices & Services > Add Integration**, select `MantelMount Remote`, and enter your device’s IP address and port (default: 81).
5. Entities like `switch.mantel_mount_up` will be created.

## Prerequisites

- Install the [MantelMount Remote Dashboard](https://github.com/jliggero/mantel-mount-remote-dashboard) for the Lovelace card.

## Notes

- Requires Home Assistant 2023.9.0 or later.
- Ensure your MantelMount device is on the same network and accessible via UDP.