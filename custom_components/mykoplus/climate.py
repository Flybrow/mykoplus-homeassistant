from __future__ import annotations
from typing import Any
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import MykoPlusConfigEntry
from .api.const import DP_CURRENT_TEMP, DP_POWER, DP_TARGET_TEMP
from .entity import MykoPlusEntity

async def async_setup_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities((MykoPlusClimate(coordinator, device_id) for device_id, device in coordinator.data.items() if device.is_climate))

class MykoPlusClimate(MykoPlusEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF

    @property
    def unique_id(self) -> str:
        return f'{self._device_id}_climate'

    @property
    def current_temperature(self) -> float | None:
        dev = self.device
        v = dev.get(DP_CURRENT_TEMP) if dev else None
        return float(v) if v is not None else None

    @property
    def target_temperature(self) -> float | None:
        dev = self.device
        v = dev.get(DP_TARGET_TEMP) if dev else None
        return float(v) if v is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        dev = self.device
        if dev and DP_POWER in dev.state and (not dev.state[DP_POWER]):
            return HVACMode.OFF
        return HVACMode.HEAT

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.coordinator.client.set_parameters([self._device_id], {DP_TARGET_TEMP: temp})
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.client.set_parameters([self._device_id], {DP_POWER: hvac_mode != HVACMode.OFF})
        self.coordinator.async_set_updated_data(dict(self.coordinator.client.devices))
