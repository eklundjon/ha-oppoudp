"""OppoController — event hub + command layer backed by OppoConnection.

Replaces the vendored SDK's OppoClient (connection/event/reconnect) and the
integration's OppoUdpManager (reconnect + entity dispatch). OppoConnection owns
the transport and the single reconnect loop; OppoController owns the OppoDevice
state model, parses incoming lines into it, sends commands (paced so bursts
don't overrun the device's small buffer), and dispatches connection/state
signals to entities.

To OppoDevice it presents the small "client" surface the device binds to
(add_event_handler / async_event / async_send_command / loop). To the entities
it presents the same manager surface they already read (device / online /
config_entry) plus the SIGNAL_* dispatches, so the entity layer is unchanged.

This module is a pure addition in this step; wiring it in (and retiring
OppoUdpManager) is the next step. See docs/ARCHITECTURE.md.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .connection import OppoConnection
from .const import (
    DEFAULT_PORT,
    SIGNAL_CLIENT_CREATED,
    SIGNAL_CONNECTED,
    SIGNAL_DISCONNECTED,
)
from .oppoudpsdk import OppoDevice
from .oppoudpsdk.command import OppoCommand
from .oppoudpsdk.const import (
    EVENT_CONNECTED,
    EVENT_DISCONNECTED,
    EVENT_MESSAGE_RECEIVED,
)
from .oppoudpsdk.response import get_response

_LOGGER = logging.getLogger(__name__)

CONF_URL = "url"
# Pacing between consecutive commands. The device caps commands at ~25 bytes and
# asks callers to "allow time for processing" (docs/PROTOCOL.md); a burst of
# ~20 state queries on connect/power-on is spread out rather than fired at once.
SEND_INTERVAL = 0.05


def entry_url(config_entry: ConfigEntry) -> str:
    """Resolve the serialx URL for an entry, migrating legacy host/port data.

    New/reconfigured entries store a serialx ``url``; existing ones hold
    ``host``/``port`` and are mapped to ``socket://host:port`` with no re-add.
    """
    url = config_entry.data.get(CONF_URL)
    if url:
        return url
    host = config_entry.data[CONF_HOST]
    port = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
    return f"socket://{host}:{port}"


class OppoController:
    """Owns the connection + device and bridges them to Home Assistant."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self._hass = hass
        self._config_entry = config_entry
        self._conn = OppoConnection(entry_url(config_entry))
        self._conn.set_handlers(
            on_message=self._on_line,
            on_connection_lost=self._on_lost,
            on_connection_restored=self._on_restored,
        )
        self._event_handlers: dict[str, list[Callable]] = defaultdict(list)
        # OppoDevice binds its handlers onto us during construction, so the
        # event registry must already exist.
        self._device = OppoDevice(self)
        self._msg_queue: asyncio.Queue[str] = asyncio.Queue()
        self._msg_task: asyncio.Task | None = None

    # ── manager-facing surface (what entities read) ────────────────────────────

    @property
    def device(self) -> OppoDevice:
        return self._device

    @property
    def online(self) -> bool:
        return self._conn.connected

    @property
    def config_entry(self) -> ConfigEntry:
        return self._config_entry

    @property
    def hass(self) -> HomeAssistant:
        return self._hass

    # ── client-facing surface (what OppoDevice binds to) ───────────────────────

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._hass.loop

    @property
    def event_handlers(self) -> dict[str, list[Callable]]:
        return self._event_handlers

    def add_event_handler(self, event: str, callback: Callable, disposable: bool = False) -> None:
        self._event_handlers[event].append(callback)

    def remove_event_handler(self, event: str, callback: Callable) -> None:
        try:
            self._event_handlers[event].remove(callback)
        except ValueError:
            _LOGGER.debug("Handler for %s was not registered", event)

    def clear_event_handlers(self) -> None:
        self._event_handlers = defaultdict(list)

    async def async_event(self, event: str, *args, **kwargs) -> None:
        """Fire an event to its handlers, awaited and error-isolated.

        Unlike the SDK's fire-and-forget async_event, handlers are awaited in
        order and one failing handler cannot take down the others or lose its
        traceback.
        """
        for callback in list(self._event_handlers.get(event, [])):
            try:
                await callback(*args, **kwargs)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error in %s handler", event)

    async def async_send_command(self, command: OppoCommand) -> None:
        """Send an SDK command object (paced). Responses arrive via the read loop."""
        await self._conn.send_bytes(command.encode())
        await asyncio.sleep(SEND_INTERVAL)

    # ── lifecycle ──────────────────────────────────────────────────────────────

    async def async_start(self) -> None:
        """Connect, wire entities, and pull an initial state snapshot."""
        self._msg_task = self._hass.loop.create_task(self._process_messages())
        await self._conn.start()
        # Entities bind their EVENT_DEVICE_STATE_UPDATED handler onto us here.
        self._dispatch(SIGNAL_CLIENT_CREATED, self)
        await self.async_event(EVENT_CONNECTED, self)
        self._dispatch(SIGNAL_CONNECTED, self._device)
        await self._device.async_request_update()

    async def disconnect(self) -> None:
        """Stop the connection and the message pump."""
        await self._conn.stop()
        if self._msg_task:
            self._msg_task.cancel()
            try:
                await self._msg_task
            except asyncio.CancelledError:
                pass
            self._msg_task = None

    # ── internals ──────────────────────────────────────────────────────────────

    def _on_line(self, line: str) -> None:
        # Called from the connection read loop; queue for ordered async handling.
        self._msg_queue.put_nowait(line)

    async def _process_messages(self) -> None:
        """Parse queued lines and feed them to the device, in order."""
        while True:
            line = await self._msg_queue.get()
            try:
                response = get_response((line + "\r").encode())
                await self.async_event(EVENT_MESSAGE_RECEIVED, response)
            except Exception:  # noqa: BLE001 — one bad line must not stop the pump
                _LOGGER.debug("Failed to process %r", line, exc_info=True)
            finally:
                self._msg_queue.task_done()

    def _on_lost(self) -> None:
        self._dispatch(SIGNAL_DISCONNECTED)
        self._hass.loop.create_task(self.async_event(EVENT_DISCONNECTED, self))

    def _on_restored(self) -> None:
        self._dispatch(SIGNAL_CONNECTED, self._device)
        self._hass.loop.create_task(self.async_event(EVENT_CONNECTED, self))
        # The device only pushes on change, so re-pull a full snapshot.
        self._hass.loop.create_task(self._device.async_request_update())

    def _dispatch(self, signal: str, *args) -> None:
        async_dispatcher_send(
            self._hass, f"{signal}_{self._config_entry.entry_id}", *args
        )
