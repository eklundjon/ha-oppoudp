"""The Oppo UDP-20x Integration"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS
from .manager import OppoUdpManager

OppoConfigEntry = ConfigEntry[OppoUdpManager]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: OppoConfigEntry):
    """Set up the component."""

    manager = OppoUdpManager(hass, entry)
    entry.runtime_data = manager

    async def on_hass_stop(event):
        """Stop updates when hass stops"""
        await manager.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
    )

    async def setup_platforms():
        """Set up platforms and initiate connection."""
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        await manager.async_start_client()

    hass.async_create_task(setup_platforms())

    return True

async def async_unload_entry(hass: HomeAssistant, entry: OppoConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.disconnect()

    return unload_ok
