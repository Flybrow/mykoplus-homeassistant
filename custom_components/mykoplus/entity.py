from __future__ import annotations
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import MykoDevice
from .const import DOMAIN
from .coordinator import MykoPlusCoordinator

class MykoPlusEntity(CoordinatorEntity[MykoPlusCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MykoPlusCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device(self) -> MykoDevice | None:
        return self.coordinator.data.get(self._device_id)

    @property
    def available(self) -> bool:
        dev = self.device
        return super().available and dev is not None and dev.connected

    @property
    def device_info(self) -> DeviceInfo:
        dev = self.device
        return DeviceInfo(identifiers={(DOMAIN, self._device_id)}, name=dev.name if dev else self._device_id, manufacturer='Myko+', model=dev.reference or dev.model if dev else None, serial_number=dev.serial_number if dev else None)
