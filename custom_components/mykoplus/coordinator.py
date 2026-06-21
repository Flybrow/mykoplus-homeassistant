from __future__ import annotations
import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import MykoDevice, MykoPlusClient
from .api.exceptions import MykoPlusApiError, MykoPlusAuthError, MykoPlusError
from .api.realtime import MykoRealtime
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
_LOGGER = logging.getLogger(__name__)

class MykoPlusCoordinator(DataUpdateCoordinator[dict[str, MykoDevice]]):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: MykoPlusClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL)
        self.entry = entry
        self.client = client
        self._realtimes: list[MykoRealtime] = []

    async def _async_update_data(self) -> dict[str, MykoDevice]:
        try:
            await self.client.async_ensure_token()
            await self.client.get_devices()
        except MykoPlusAuthError as err:
            raise UpdateFailed(f'Auth Myko+ échouée : {err}') from err
        except MykoPlusApiError as err:
            raise UpdateFailed(f'API Myko+ : {err}') from err
        except MykoPlusError as err:
            raise UpdateFailed(f'Erreur Myko+ : {err}') from err
        return dict(self.client.devices)

    async def async_start_realtime(self) -> None:
        token = self.client.token
        if not token:
            return
        for home_id in self.client.homes:
            rt = MykoRealtime(token, home_id, self._handle_event)
            try:
                await rt.start()
            except Exception as err:
                _LOGGER.warning('Temps réel indisponible (home %s): %s', home_id, err)
                continue
            self._realtimes.append(rt)

    async def async_stop_realtime(self) -> None:
        for rt in self._realtimes:
            await rt.stop()
        self._realtimes.clear()

    @callback
    def _handle_event(self, home_id: str, event: str, data: Any) -> None:
        if event != 'setState' or not isinstance(data, dict):
            return
        if data.get('objectType') != 'device':
            return
        device_id = data.get('objectId')
        state = data.get('data')
        if not device_id or not isinstance(state, dict):
            return
        if self.client.apply_state_event(device_id, state):
            self.async_set_updated_data(dict(self.client.devices))
