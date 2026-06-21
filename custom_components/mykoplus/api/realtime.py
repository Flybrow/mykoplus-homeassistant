from __future__ import annotations
import logging
from collections.abc import Callable
from typing import Any
import socketio
from . import const
_LOGGER = logging.getLogger(__name__)
EventCallback = Callable[[str, str, Any], None]

class _CatchAllClient(socketio.AsyncClient):

    def __init__(self, home_id: str, on_event: EventCallback, **kw: Any) -> None:
        super().__init__(**kw)
        self._home_id = home_id
        self._on_event = on_event

    async def _trigger_event(self, event: str, namespace: str, *args: Any) -> Any:
        if event not in ('connect', 'disconnect', 'connect_error'):
            try:
                self._on_event(self._home_id, event, args[0] if args else None)
            except Exception:
                _LOGGER.exception('callback temps réel a échoué')
        return await super()._trigger_event(event, namespace, *args)

class MykoRealtime:

    def __init__(self, token: str, home_id: str, on_event: EventCallback) -> None:
        self._token = token
        self._home_id = home_id
        self._on_event = on_event
        self._sio = _CatchAllClient(home_id, on_event, reconnection=True, reconnection_attempts=0, logger=False, engineio_logger=False)

        @self._sio.event
        async def connect() -> None:
            _LOGGER.debug('socket.io connecté (home %s)', home_id)

        @self._sio.event
        async def disconnect() -> None:
            _LOGGER.debug('socket.io déconnecté (home %s)', home_id)

    def update_token(self, token: str) -> None:
        self._token = token

    @property
    def home_id(self) -> str:
        return self._home_id

    def is_connected(self) -> bool:
        return self._sio.connected

    async def start(self) -> None:
        headers = dict(const.APP_HEADERS)
        headers['authorization'] = f'Bearer {self._token}'
        url = f'{const.WS_BASE}?homeId={self._home_id}'
        await self._sio.connect(url, headers=headers, socketio_path='socket.io-v2', transports=['websocket'], wait_timeout=15)

    async def stop(self) -> None:
        try:
            await self._sio.disconnect()
        except Exception:
            pass
