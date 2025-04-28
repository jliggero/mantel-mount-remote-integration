import asyncio
import logging
import socket
import time
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Delay (seconds) before momentary switches turn off
AUTO_RESET_DELAY = 1
# Debounce delay (seconds) to prevent rapid triggers
DEBOUNCE_DELAY = 2
# Interval (seconds) between UDP packets for directional switches
PACKET_INTERVAL = 0.124
# Timeout (seconds) for directional switches to auto-stop
AUTO_STOP_TIMEOUT = 5

# Keys in config entry
IP_KEY = "ip_address"
PORT_KEY = "port"

# Configuration of each switch and its behavior
SWITCH_CONFIG = {
    "up":      {"type": "directional", "command": "MMJ2\r", "friendly_name": "Mantel Mount Up"},
    "down":    {"type": "directional", "command": "MMJ4\r", "friendly_name": "Mantel Mount Down"},
    "left":    {"type": "directional", "command": "MMJ3\r", "friendly_name": "Mantel Mount Left"},
    "right":   {"type": "directional", "command": "MMJ1\r", "friendly_name": "Mantel Mount Right"},
    "stop":    {"type": "momentary",  "command": "MMJ0\r", "friendly_name": "Mantel Mount Stop"},
    "home":    {"type": "momentary",  "command": "MMR0\r", "friendly_name": "Mantel Mount Home"},
    "preset_1":{"type": "momentary",  "command": "MMR1\r", "friendly_name": "Mantel Mount Preset 1"},
    "preset_2":{"type": "momentary",  "command": "MMR2\r", "friendly_name": "Mantel Mount Preset 2"},
    "preset_3":{"type": "momentary",  "command": "MMR3\r", "friendly_name": "Mantel Mount Preset 3"},
    "save_1":  {"type": "momentary",  "command": "MMS1\r", "friendly_name": "Mantel Mount Save 1"},
    "save_2":  {"type": "momentary",  "command": "MMS2\r", "friendly_name": "Mantel Mount Save 2"},
    "save_3":  {"type": "momentary",  "command": "MMS3\r", "friendly_name": "Mantel Mount Save 3"},
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback = None) -> None:
    """Set up Mantel Mount switches from a config entry."""
    _LOGGER.debug(f"Calling async_setup_entry with hass={hass}, entry={entry}, async_add_entities={async_add_entities}")
    if async_add_entities is None:
        _LOGGER.error("async_add_entities is None, expected a callback function")
        raise ValueError("async_add_entities is required for platform setup")

    ip = hass.data[DOMAIN][entry.entry_id]["ip_address"]
    port = hass.data[DOMAIN][entry.entry_id]["port"]

    if not ip or not port:
        raise ValueError("IP address and port are required in the configuration.")

    entities = []
    for key, cfg in SWITCH_CONFIG.items():
        entity_id = f"switch.mantel_mount_{key}"
        if cfg["type"] == "directional":
            entities.append(
                MantelMountDirectionalSwitch(entity_id, cfg["friendly_name"], cfg["command"], ip, port)
            )
        else:
            entities.append(
                MantelMountMomentarySwitch(entity_id, cfg["friendly_name"], cfg["command"], ip, port)
            )

    async_add_entities(entities)

class MantelMountMomentarySwitch(SwitchEntity):
    """Momentary switch that sends a single UDP command and resets."""

    def __init__(self, entity_id: str, friendly_name: str, command: str, ip: str, port: int) -> None:
        self.entity_id = entity_id
        self._attr_name = friendly_name
        self._attr_unique_id = entity_id
        self._command = command.encode()
        self._ip = ip
        self._port = port
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        _LOGGER.debug(f"Sending momentary command for {self._attr_name}")
        try:
            await asyncio.to_thread(self._send_udp)
        except Exception as e:
            _LOGGER.error(f"Error sending UDP command {self._command}: {e}")

        self._is_on = True
        self.async_write_ha_state()
        await asyncio.sleep(AUTO_RESET_DELAY)
        self._is_on = False
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        if self._is_on:
            self._is_on = False
            self.async_write_ha_state()

    def _send_udp(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Send command multiple times for reliability
            sock.sendto(self._command, (self._ip, self._port))
            time.sleep(0.1)
            sock.sendto(self._command, (self._ip, self._port))
            time.sleep(0.1)
            sock.sendto(self._command, (self._ip, self._port))
            _LOGGER.debug(f"Sent UDP command {self._command} to {self._ip}:{self._port}")
        finally:
            sock.close()

class MantelMountDirectionalSwitch(SwitchEntity):
    """Directional switch that sends continuous UDP commands while on."""

    def __init__(self, entity_id: str, friendly_name: str, command: str, ip: str, port: int) -> None:
        self.entity_id = entity_id
        self._attr_name = friendly_name
        self._attr_unique_id = entity_id
        self._command = command.encode()
        self._ip = ip
        self._port = port
        self._is_on = False
        self._last_trigger = 0  # Timestamp for debouncing
        self._send_task = None  # Task for continuous sending
        self._stop_command = b"MMJ0\r"  # Stop command

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        current_time = time.time()
        if current_time - self._last_trigger < DEBOUNCE_DELAY:
            _LOGGER.debug(f"Debouncing rapid trigger for {self._attr_name}")
            return
        self._last_trigger = current_time

        if self._is_on:
            _LOGGER.debug(f"{self._attr_name} already on, ignoring")
            return

        _LOGGER.debug(f"Starting continuous command for {self._attr_name}")
        self._is_on = True
        self.async_write_ha_state()

        # Start background task to send packets with auto-stop
        if self._send_task is None or self._send_task.done():
            self._send_task = asyncio.create_task(self._send_continuous())

    async def async_turn_off(self, **kwargs) -> None:
        if not self._is_on:
            _LOGGER.debug(f"{self._attr_name} already off, ignoring")
            return

        _LOGGER.debug(f"Stopping continuous command for {self._attr_name}")
        self._is_on = False
        self.async_write_ha_state()

        # Cancel sending task
        if self._send_task and not self._send_task.done():
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                _LOGGER.debug(f"Send task cancelled for {self._attr_name}")

        # Send stop command
        try:
            await asyncio.to_thread(self._send_stop)
        except Exception as e:
            _LOGGER.error(f"Error sending stop command for {self._attr_name}: {e}")

    async def _send_continuous(self):
        """Send UDP packets continuously while switch is on."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            start_time = time.time()
            while self._is_on and (time.time() - start_time) < AUTO_STOP_TIMEOUT:
                sock.sendto(self._command, (self._ip, self._port))
                _LOGGER.debug(f"Sent UDP command {self._command} to {self._ip}:{self._port}")
                await asyncio.sleep(PACKET_INTERVAL)
            if self._is_on:
                _LOGGER.debug(f"Auto-stopping {self._attr_name} after {AUTO_STOP_TIMEOUT}s")
                self._is_on = False
                self.async_write_ha_state()
                await asyncio.to_thread(self._send_stop)
        except Exception as e:
            _LOGGER.error(f"Error in continuous send for {self._attr_name}: {e}")
        finally:
            sock.close()
            _LOGGER.debug(f"Closed socket for {self._attr_name}")

    def _send_stop(self):
        """Send stop command multiple times for reliability."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Send stop command three times
            sock.sendto(self._stop_command, (self._ip, self._port))
            time.sleep(0.1)
            sock.sendto(self._stop_command, (self._ip, self._port))
            time.sleep(0.1)
            sock.sendto(self._stop_command, (self._ip, self._port))
            _LOGGER.debug(f"Sent stop command {self._stop_command} to {self._ip}:{self._port}")
        finally:
            sock.close()