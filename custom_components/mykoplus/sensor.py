from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import MykoPlusConfigEntry
from .api import MykoDevice
from .api.const import DP_BATTERY, DP_CURRENT_TEMP, DP_HUMIDITY
from .entity import MykoPlusEntity

@dataclass(frozen=True, kw_only=True)
class MykoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[MykoDevice], float | None]

def _num(dev: MykoDevice, key: str) -> float | None:
    v = dev.get(key)
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
SENSORS: tuple[MykoSensorDescription, ...] = (MykoSensorDescription(key='current_temperature', value_fn=lambda d: _num(d, DP_CURRENT_TEMP), device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS), MykoSensorDescription(key='battery', value_fn=lambda d: _num(d, DP_BATTERY), device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE), MykoSensorDescription(key='humidity', value_fn=lambda d: _num(d, DP_HUMIDITY), device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE))

async def async_setup_entry(hass: HomeAssistant, entry: MykoPlusConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[MykoPlusSensor] = []
    for device_id, device in coordinator.data.items():
        for desc in SENSORS:
            if desc.value_fn(device) is not None:
                entities.append(MykoPlusSensor(coordinator, device_id, desc))
    async_add_entities(entities)

class MykoPlusSensor(MykoPlusEntity, SensorEntity):
    entity_description: MykoSensorDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_translation_key = description.key

    @property
    def unique_id(self) -> str:
        return f'{self._device_id}_{self.entity_description.key}'

    @property
    def native_value(self) -> float | None:
        dev = self.device
        return self.entity_description.value_fn(dev) if dev else None
