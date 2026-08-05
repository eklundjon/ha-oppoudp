"""Base Entity for the Oppo UDP-20x integration."""

import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_CLIENT_CREATED, SIGNAL_CONNECTED, SIGNAL_DISCONNECTED
from .manager import OppoUdpManager
from .oppoudpsdk import OppoDevice

_LOGGER = logging.getLogger(__name__)

class OppoUdpEntity(Entity):
    """
    Base class for Oppo Home Assistant entities
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, host: str, name: str, identifier: str, manager: OppoUdpManager):
        self._host = host
        self._name = name
        self._identifier = identifier
        self._manager = manager
        self._attr_unique_id = identifier

    @property
    def device(self) -> OppoDevice:
        return self._manager.device

    @property
    def available(self) -> bool:
        return self._manager.online

    @property
    def host(self):
        """Return the host name of the device."""
        return self._host

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        info = DeviceInfo(
            identifiers={(DOMAIN, self._identifier)},
            name=self._manager.config_entry.title,
            manufacturer="Oppo",
            model="UDP-20x",
        )
        if self._manager.device:
            info["sw_version"] = self._manager.device.firmware_version

        return info

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""

        @callback
        def _async_connected(device):
            """Handle that a connection was made to a device."""
            self.async_device_connected(device)
            self.async_write_ha_state()

        @callback
        def _async_disconnected():
            """Handle that a connection to a device was lost."""
            self.async_device_disconnected()
            self.async_write_ha_state()

        @callback
        def _async_client_created(client):
            """Handle when a client is created (due to reconnect)."""
            self.async_client_created(client)
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{SIGNAL_CONNECTED}_{self._identifier}", _async_connected
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{SIGNAL_CLIENT_CREATED}_{self._identifier}", _async_client_created
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{SIGNAL_DISCONNECTED}_{self._identifier}", _async_disconnected
            )
        )

    def async_device_connected(self, device):
        """Handle when connection is made to device."""

    def async_device_disconnected(self):
        """Handle when connection was lost to device."""

    def async_client_created(self, client):
        """Handle when a new client is created (due to reconnections)."""
