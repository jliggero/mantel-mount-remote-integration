# MantelMount Remote Integration

**MantelMount Remote** is a custom Home Assistant integration that enables control of MantelMount lift systems directly from Home Assistant, including directional movement, presets, and save positions.

<div align="center">
  <img src="https://github.com/jliggero/mantel-mount-remote-integration/raw/main/brands/mantel_mount_remote/logo.svg" width="200" alt="MantelMount Logo" />
</div>

---

## Features
- Move MantelMount **up, down, left, right**.
- **Stop** movement at any time.
- Return to **Home** position.
- Support for **three preset positions** and **three save slots**.
- Full local control over your MantelMount via UDP.

---

## Installation
1. Add this repository to HACS:
   - Go to HACS → Integrations → Three Dots Menu → **Custom Repositories**.
   - URL: `https://github.com/jliggero/mantel-mount-remote-integration`
   - Category: **Integration**
2. Install the **MantelMount Remote** integration.
3. Restart Home Assistant.
4. Set up the integration through **Settings → Devices & Services → Add Integration → MantelMount Remote**.

---

## Notes
- This integration **requires** installing the matching **Dashboard card** for full remote control from the Lovelace UI.
- See: [MantelMount Remote Dashboard](https://github.com/jliggero/mantel-mount-remote-dashboard).

---

## Links
- [Dashboard Card Repository](https://github.com/jliggero/mantel-mount-remote-dashboard)
- [Author: jliggero](https://github.com/jliggero)
