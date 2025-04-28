"""Init file for MantelMount Remote Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mantel_mount_remote"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the MantelMount Remote integration."""
    return True  # Nothing needed here for config flow setups

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MantelMount Remote from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "ip_address": entry.data["ip_address"],
        "port": entry.data["port"]
    }
    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])
    _LOGGER.info("MantelMount Remote setup complete")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_forward_entry_unloads(entry, ["switch"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
