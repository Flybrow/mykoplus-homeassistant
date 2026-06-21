from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from . import const
from .const import DP_POWER

@dataclass
class MykoHome:
    home_id: str
    name: str
    device_ids: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> 'MykoHome':
        return cls(home_id=str(data.get('_id') or data.get('id') or ''), name=data.get('name') or 'Maison', device_ids=[str(d) for d in data.get('devices', [])], raw=data)

@dataclass
class MykoDevice:
    device_id: str
    name: str
    home_id: str = ''
    model: str = ''
    reference: str = ''
    serial_number: str = ''
    connected: bool = False
    state: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_power(self) -> bool:
        return DP_POWER in self.state

    @property
    def is_light(self) -> bool:
        return const.DP_BRIGHTNESS in self.state

    @property
    def is_climate(self) -> bool:
        return const.DP_TARGET_TEMP in self.state

    @property
    def is_plug(self) -> bool:
        return self.has_power and (not self.is_light) and (not self.is_climate)

    @property
    def is_on(self) -> bool | None:
        val = self.state.get(DP_POWER)
        return bool(val) if val is not None else None

    def get(self, key: str, default: Any=None) -> Any:
        return self.state.get(key, default)

    @classmethod
    def from_api(cls, data: dict[str, Any], home_id: str='') -> 'MykoDevice':
        state = data.get('state') or {}
        if not isinstance(state, dict):
            state = {}
        return cls(device_id=str(data.get('_id') or data.get('id') or ''), name=data.get('name') or data.get('profile_name') or 'Appareil Myko+', home_id=home_id or str(data.get('home') or ''), model=data.get('model') or '', reference=data.get('reference') or '', serial_number=data.get('serial_number') or '', connected=bool(data.get('connected', False)), state=dict(state), raw=data)

    def update_state(self, new_state: dict[str, Any]) -> None:
        if isinstance(new_state, dict):
            self.state.update(new_state)
