"""Protocol/enum audit.

Locks the vendored SDK's enum *values* to the exact wire strings the player
sends (per docs/PROTOCOL.md). This class of bug — right code, wrong string,
e.g. HOME_MENU — is invisible to a coverage check and froze the entity on
hardware, so it gets its own guard.
"""
from __future__ import annotations

import pytest

from custom_components.oppo_udp.oppoudpsdk import DiscType, PlayStatus


@pytest.mark.parametrize(
    "raw",
    [
        "PLAY", "PAUSE", "STOP", "HOME MENU", "MEDIA CENTER",
        "SCREEN SAVER", "DISC MENU", "SETUP", "OPEN", "CLOSE",
    ],
)
def test_playstatus_parses_wire_strings(raw):
    assert PlayStatus(raw)


def test_home_menu_value_has_space():
    # Regression for the frozen-entity bug: the player emits "HOME MENU".
    assert PlayStatus.HOME_MENU.value == "HOME MENU"


def test_menu_statuses_use_spaces_not_underscores():
    for member in (
        PlayStatus.HOME_MENU,
        PlayStatus.MEDIA_CENTER,
        PlayStatus.SCREEN_SAVER,
        PlayStatus.DISC_MENU,
    ):
        assert " " in member.value and "_" not in member.value


@pytest.mark.parametrize(
    "raw",
    ["BD-MV", "DVD-VIDEO", "DVD-AUDIO", "SACD", "CDDA", "UHBD", "NO-DISC"],
)
def test_disctype_parses_wire_strings(raw):
    assert DiscType(raw)
