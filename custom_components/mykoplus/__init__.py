from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import MykoPlusClient
from .api.exceptions import MykoPlusAuthError, MykoPlusError
from .const import CONF_EMAIL, CONF_PASSWORD, PLATFORMS
from .coordinator import MykoPlusCoordinator
type MykoPlusConfigEntry = ConfigEntry[MykoPlusCoordinator]

async def async_setup_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry) -> bool:
    client = MykoPlusClient(email=entry.data[CONF_EMAIL], password=entry.data[CONF_PASSWORD], session=async_get_clientsession(hass))
    try:
        await client.login()
        await coordinator_first_refresh(hass, entry, client)
    except MykoPlusAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except MykoPlusError as err:
        raise ConfigEntryNotReady(str(err)) from err
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await entry.runtime_data.async_start_realtime()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True

async def coordinator_first_refresh(hass: HomeAssistant, entry: MykoPlusConfigEntry, client: MykoPlusClient) -> None:
    coordinator = MykoPlusCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

async def async_unload_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry) -> bool:
    await entry.runtime_data.async_stop_realtime()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def _async_update_listener(hass: HomeAssistant, entry: MykoPlusConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
