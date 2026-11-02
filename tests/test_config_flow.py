"""Config flow: Bluetooth discovery asks before adding the logger.

Requires homeassistant (config_flow.py imports it). The flow runs against a
minimal stand-in for hass.config_entries: no entries, no other flows.
"""
from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace

import pytest

pytest.importorskip("homeassistant")

from homeassistant.data_entry_flow import FlowResultType

from custom_components.deye_ble.config_flow import DeyeBleConfigFlow
from custom_components.deye_ble.const import CONF_ADDRESS, CONF_LOGGER_SN, DOMAIN

ADDRESS = "68:79:C4:C4:64:BF"
SN = "D25724366040"


class _FlowManager:
    def async_progress_by_handler(self, handler, include_uninitialized=False, match_context=None):
        return []


class _ConfigEntries:
    flow = _FlowManager()

    def async_entry_for_domain_unique_id(self, domain, unique_id):
        return None


def _flow(source: str) -> DeyeBleConfigFlow:
    flow = DeyeBleConfigFlow()
    flow.hass = SimpleNamespace(config_entries=_ConfigEntries())
    flow.handler = DOMAIN
    flow.flow_id = "flow"
    flow.context = {"source": source}
    return flow


@pytest.mark.asyncio
async def test_discovery_asks_before_adding_even_with_a_valid_serial():
    # A logger in range must not start being polled until someone says so: the
    # held radio starves its Wi-Fi and locks out the phone app.
    flow = _flow("bluetooth")
    result = await flow.async_step_bluetooth(SimpleNamespace(name=SN, address=ADDRESS))
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    default = next(k.default() for k in result["data_schema"].schema if k == CONF_LOGGER_SN)
    assert default == SN


@pytest.mark.asyncio
async def test_confirming_a_discovery_adds_the_logger():
    flow = _flow("bluetooth")
    await flow.async_step_bluetooth(SimpleNamespace(name=SN, address=ADDRESS))
    result = await flow.async_step_confirm({CONF_LOGGER_SN: SN})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ADDRESS: ADDRESS, CONF_LOGGER_SN: SN}


def test_translations_match_strings():
    # Custom integrations get UI text only from translations/<lang>.json; HA
    # never reads strings.json for them.
    root = pathlib.Path(__file__).parent.parent / "custom_components" / DOMAIN
    strings = json.loads((root / "strings.json").read_text())
    assert json.loads((root / "translations" / "en.json").read_text()) == strings
