from __future__ import annotations
import logging
from typing import Any
import aiohttp
from . import const
from .exceptions import MykoPlusApiError, MykoPlusAuthError, MykoPlusConnectionError
from .models import MykoDevice, MykoHome
_LOGGER = logging.getLogger(__name__)

class MykoPlusClient:

    def __init__(self, email: str, password: str, *, session: aiohttp.ClientSession | None=None) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._owns_session = session is None
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._user_id: str | None = None
        self._homes: dict[str, MykoHome] = {}
        self._devices: dict[str, MykoDevice] = {}

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and (not self._session.closed):
            await self._session.close()

    async def __aenter__(self) -> 'MykoPlusClient':
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _request(self, method: str, path: str, *, body: dict[str, Any] | None=None, auth: bool=True, _retry: int=2) -> Any:
        session = await self._ensure_session()
        headers = dict(const.APP_HEADERS)
        headers['user-agent'] = const.USER_AGENT
        headers['content-type'] = 'application/json'
        if auth:
            if not self._token:
                await self.login()
            headers['authorization'] = f'Bearer {self._token}'
        url = f'{const.API_BASE}{path}'
        try:
            async with session.request(method, url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=const.DEFAULT_TIMEOUT)) as resp:
                status = resp.status
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise MykoPlusConnectionError(str(err)) from err
        except TimeoutError as err:
            raise MykoPlusConnectionError('timeout') from err
        if status == 401:
            if auth and _retry > 0:
                self._token = None
                await self.login()
                return await self._request(method, path, body=body, auth=auth, _retry=_retry - 1)
            raise MykoPlusAuthError('token expiré ou invalide (401)')
        if status >= 400:
            raise MykoPlusApiError(status, None, text[:200])
        if not text:
            return None
        import json as _json
        try:
            return _json.loads(text)
        except ValueError:
            return text

    async def login(self) -> None:
        data = await self._request('POST', const.EP_LOGIN, body={'email': self._email, 'password': self._password}, auth=False)
        if not isinstance(data, dict) or 'token' not in data:
            raise MykoPlusAuthError('réponse de login inattendue')
        self._token = data['token']
        self._refresh_token = data.get('refresh_token')
        self._user_id = data.get('id')
        _LOGGER.debug('Login Myko+ ok (user %s)', self._user_id)

    async def async_ensure_token(self) -> None:
        if not self._token:
            await self.login()

    async def get_homes(self) -> list[MykoHome]:
        if not self._user_id:
            await self.login()
        data = await self._request('GET', const.EP_USER_HOMES.format(user_id=self._user_id))
        items = data.get('homes', []) if isinstance(data, dict) else data or []
        homes = [MykoHome.from_api(h) for h in items]
        self._homes = {h.home_id: h for h in homes}
        return homes

    async def get_devices(self) -> list[MykoDevice]:
        if not self._homes:
            await self.get_homes()
        devices: list[MykoDevice] = []
        for home_id in self._homes:
            data = await self._request('GET', const.EP_HOME_DEVICES.format(home_id=home_id))
            items = data if isinstance(data, list) else data.get('devices', [])
            devices.extend((MykoDevice.from_api(d, home_id) for d in items))
        self._devices = {d.device_id: d for d in devices}
        return devices

    async def set_parameters(self, device_ids: list[str], parameters: dict[str, Any]) -> None:
        await self._request('PATCH', const.EP_DEVICES_STATE, body={'deviceIdList': device_ids, 'parameters': parameters})
        for did in device_ids:
            if did in self._devices:
                self._devices[did].update_state(parameters)

    async def async_set_power(self, device_id: str, on: bool) -> None:
        await self.set_parameters([device_id], {const.DP_POWER: on})

    async def turn_on(self, device_id: str) -> None:
        await self.async_set_power(device_id, True)

    async def turn_off(self, device_id: str) -> None:
        await self.async_set_power(device_id, False)

    @property
    def devices(self) -> dict[str, MykoDevice]:
        return self._devices

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def homes(self) -> dict[str, 'MykoHome']:
        return self._homes

    def apply_state_event(self, device_id: str, state: dict[str, Any]) -> bool:
        dev = self._devices.get(device_id)
        if dev is None:
            return False
        dev.update_state(state)
        return True
