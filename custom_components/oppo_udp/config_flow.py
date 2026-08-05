""" ConfigFlow for the Oppo UDP-20x Integration """
from __future__ import annotations

import ipaddress
import logging
import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_PORT, DOMAIN
from .exceptions import HaAlreadyConfigured, HaCannotConnect, HaInvalidHost
from .oppoudpsdk import OppoClient

_LOGGER = logging.getLogger(__name__)

def _data_schema(host: str = "", port: int = DEFAULT_PORT) -> vol.Schema:
    """Build the host/port schema, optionally pre-filled for reconfigure."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_PORT, default=port): int,
        }
    )

def host_valid(host: str) -> bool:
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version in (4, 6):
            return True
    except ValueError:
        pass
    if len(host) > 253:
        return False
    allowed = re.compile(r"(?!-)[A-Z\d\-\_]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in host.split("."))

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oppo UDP-20x."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                await self._validate(user_input)
            except HaCannotConnect:
                errors[CONF_HOST] = "cannot_connect"
            except HaAlreadyConfigured:
                errors[CONF_HOST] = "already_configured"
            except HaInvalidHost:
                errors[CONF_HOST] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=_data_schema(), errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing entry (e.g. changed IP/port)."""
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                await self._validate(user_input, ignore_entry_id=entry.entry_id)
            except HaCannotConnect:
                errors[CONF_HOST] = "cannot_connect"
            except HaAlreadyConfigured:
                errors[CONF_HOST] = "already_configured"
            except HaInvalidHost:
                errors[CONF_HOST] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry, title=user_input[CONF_HOST], data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_data_schema(
                entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT)
            ),
            errors=errors,
        )

    async def _validate(self, user_input, ignore_entry_id: str | None = None) -> None:
        """Validate host, dedup, and connectivity; raise on failure."""
        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        if not host_valid(host):
            raise HaInvalidHost
        if self._host_configured(host, ignore_entry_id):
            raise HaAlreadyConfigured
        await self.test_connection(host, port)

    def _host_configured(self, host: str, ignore_entry_id: str | None = None) -> bool:
        """Return True if another entry already uses this host."""
        return any(
            entry.data.get(CONF_HOST) == host
            for entry in self._async_current_entries()
            if entry.entry_id != ignore_entry_id
        )

    async def test_connection(self, host: str, port: int) -> None:
        """Validate that we can connect to the device."""
        client = OppoClient(host, port)
        try:
            connected = await client.test_connection()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Connection test to %s:%s failed: %s", host, port, err)
            raise HaCannotConnect from err
        if not connected:
            raise HaCannotConnect
