import socket
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import callback

DOMAIN = "mantel_mount_remote"

class MantelMountConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for MantelMount Remote."""

  VERSION = 1

  async def async_step_user(self, user_input=None):
    """Handle the initial step."""
    errors = {}
    if user_input is not None:
      # Validate the IP and port by attempting a connection
      ip_address = user_input[CONF_IP_ADDRESS]
      port = user_input[CONF_PORT]
      try:
        # Test connection by sending a stop command
        stop_command = b"MMJ0\r"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(stop_command, (ip_address, port))
        sock.close()
      except Exception as e:
        errors["base"] = "cannot_connect"
      else:
        # If connection succeeds, create the config entry
        return self.async_create_entry(
          title="MantelMount Remote",
          data={
            "ip_address": ip_address,
            "port": port
          }
        )

    return self.async_show_form(
      step_id="user",
      data_schema=vol.Schema({
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_PORT, default=81): int,
      }),
      errors=errors
    )

  @staticmethod
  @callback
  def async_get_options_flow(config_entry):
    """Get the options flow for this handler."""
    return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
  """Handle options flow for MantelMount Remote."""

  def __init__(self, config_entry):
    self.config_entry = config_entry

  async def async_step_init(self, user_input=None):
    """Manage the options."""
    if user_input is not None:
      return self.async_create_entry(title="", data=user_input)

    return self.async_show_form(
      step_id="init",
      data_schema=vol.Schema({
        vol.Required(CONF_IP_ADDRESS, default=self.config_entry.data.get(CONF_IP_ADDRESS)): str,
        vol.Required(CONF_PORT, default=self.config_entry.data.get(CONF_PORT)): int,
      })
    )