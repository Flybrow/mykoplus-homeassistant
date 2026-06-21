from __future__ import annotations
from typing import Any
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import MykoPlusConfigEntry
from .api.const import BRIGHTNESS_MAX, DP_BRIGHTNESS, DP_POWER
from .entity import MykoPlusEntity

async def async_setup_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities((MykoPlusLight(coordinator, device_id) for device_id, device in coordinator.data.items() if device.is_light))

def _to_ha(v: float) -> int:
    return round(min(max(v, 0), BRIGHTNESS_MAX) / BRIGHTNESS_MAX * 255)

def _to_api(v: int) -> int:
    return round(v / 255 * BRIGHTNESS_MAX)

class MykoPlusLight(MykoPlusEntity, LightEntity):
    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def unique_id(self) -> str:
        return f'{self._device_id}_light'

    @property
    def is_on(self) -> bool | None:
        dev = self.device
        if dev is None:
            return None
        if DP_POWER in dev.state:
            return bool(dev.state[DP_POWER])
        return (dev.get(DP_BRIGHTNESS) or 0) > 0

    @property
    def brightness(self) -> int | None:
        dev = self.device
        val = dev.get(DP_BRIGHTNESS) if dev else None
        return _to_ha(float(val)) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        params: dict[str, Any] = {DP_POWER: True}
        if ATTR_BRIGHTNESS in kwargs:
            params[DP_BRIGHTNESS] = _to_api(kwargs[ATTR_BRIGHTNESS])
        await self.coordinator.client.set_parameters([self._device_id], params)
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_parameters([self._device_id], {DP_POWER: False})
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))
