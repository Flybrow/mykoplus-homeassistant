from __future__ import annotations
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import MykoPlusConfigEntry
from .api.const import DP_DARK_MODE
from .entity import MykoPlusEntity

async def async_setup_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[MykoPlusEntity] = []
    for device_id, device in coordinator.data.items():
        if device.is_plug:
            entities.append(MykoPlusSwitch(coordinator, device_id))
        if DP_DARK_MODE in device.state:
            entities.append(MykoPlusLedSwitch(coordinator, device_id))
    async_add_entities(entities)

class MykoPlusSwitch(MykoPlusEntity, SwitchEntity):
    _attr_name = None

    @property
    def unique_id(self) -> str:
        return f'{self._device_id}_power'

    @property
    def is_on(self) -> bool | None:
        dev = self.device
        return dev.is_on if dev else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.turn_on(self._device_id)
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.turn_off(self._device_id)
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))

class MykoPlusLedSwitch(MykoPlusEntity, SwitchEntity):
    _attr_translation_key = 'led'
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self) -> str:
        return f'{self._device_id}_led'

    @property
    def is_on(self) -> bool | None:
        dev = self.device
        if dev is None or DP_DARK_MODE not in dev.state:
            return None
        return not bool(dev.state[DP_DARK_MODE])

    async def _set(self, led_on: bool) -> None:
        await self.coordinator.client.set_parameters([self._device_id], {DP_DARK_MODE: not led_on})
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
