"""Tests for the Oppo UDP-20x config and reconfigure flows."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.data_entry_flow import FlowResultType

from custom_components.oppo_udp.const import DOMAIN
from tests.conftest import ENTRY_DATA, MOCK_HOST, MOCK_PORT


def _patch_client(connected=True, error=None):
    """Patch the OppoClient the flow constructs so no real socket is opened."""
    client = MagicMock()
    client.test_connection = AsyncMock(return_value=connected, side_effect=error)
    return patch("custom_components.oppo_udp.config_flow.OppoClient", return_value=client)


def _patch_setup():
    """A CREATE_ENTRY result makes HA set the entry up immediately, which would
    build a real manager/client and open a socket. Stub setup for flow tests."""
    return patch(
        "custom_components.oppo_udp.async_setup_entry", AsyncMock(return_value=True)
    )


async def test_user_success(hass):
    with _patch_client(), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": MOCK_HOST, "port": MOCK_PORT}
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_HOST
    assert result["data"] == {"host": MOCK_HOST, "port": MOCK_PORT}


async def test_user_cannot_connect(hass):
    with _patch_client(connected=False):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": MOCK_HOST, "port": MOCK_PORT}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["host"] == "cannot_connect"


async def test_user_invalid_host(hass):
    with _patch_client():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "not a host!", "port": MOCK_PORT}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["host"] == "invalid_host"


async def test_user_duplicate_host(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA).add_to_hass(hass)
    with _patch_client():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": MOCK_HOST, "port": MOCK_PORT}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["host"] == "already_configured"


async def test_reconfigure_updates_host(hass, config_entry):
    new_host = "192.168.1.99"
    with _patch_client(), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": config_entry.entry_id},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": new_host, "port": MOCK_PORT}
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data["host"] == new_host
