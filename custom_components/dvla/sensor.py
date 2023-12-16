"""DVLA sensor platform."""
from datetime import timedelta
import logging
from aiohttp import ClientError
from homeassistant.core import HomeAssistant, callback
from typing import Any
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .const import DOMAIN, CONF_REG_NUMBER
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from .coordinator import DVLACoordinator

_LOGGER = logging.getLogger(__name__)
# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=10)

SENSOR_TYPES = [
    SensorEntityDescription(
        key="registrationNumber",
        name="Registration Number",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="taxStatus",
        name="Tax Status",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="taxDueDate",
        name="Tax Due Date",
        icon="mdi:calendar-clock"
    ),
    SensorEntityDescription(
        key="motStatus",
        name="Mot Status",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="make",
        name="Make",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="yearOfManufacture",
        name="Year of Manufacture",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="engineCapacity",
        name="Engine Capacity",
        icon="mdi:engine"
    ),
    SensorEntityDescription(
        key="co2Emissions",
        name="CO2 Emissions",
        icon="mdi:engine"
    ),
    SensorEntityDescription(
        key="fuelType",
        name="Fuel Type",
        icon="mdi:engine"
    ),
    SensorEntityDescription(
        key="markedForExport",
        name="Marked for Export",
        icon="mdi:export"
    ),
    SensorEntityDescription(
        key="colour",
        name="Colour",
        icon="mdi:spray"
    ),
    SensorEntityDescription(
        key="typeApproval",
        name="Type Approval",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="revenueWeight",
        name="Revenue Weight",
        icon="mdi:weight"
    ),
    SensorEntityDescription(
        key="dateOfLastV5CIssued",
        name="Date of Last V5C Issued",
        icon="mdi:calendar"
    ),
    SensorEntityDescription(
        key="motExpiryDate",
        name="Mot Expiry Date",
        icon="mdi:calendar-check"
    ),
    SensorEntityDescription(
        key="wheelplan",
        name="Wheelplan",
        icon="mdi:car"
    ),
    SensorEntityDescription(
        key="monthOfFirstRegistration",
        name="Month of First Registration",
        icon="mdi:calendar"
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if entry.options:
        config.update(entry.options)

    session = async_get_clientsession(hass)
    coordinator = DVLACoordinator(hass, session, entry.data)

    await coordinator.async_refresh()

    name = entry.data[CONF_REG_NUMBER]

    sensors = [DVLASensor(coordinator, name, description) for description in SENSOR_TYPES]
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    coordinator = DVLACoordinator(hass, session, config)

    name = config[CONF_REG_NUMBER]

    sensors = [DVLASensor(coordinator, name, description) for description in SENSOR_TYPES]
    async_add_entities(sensors, update_before_add=True)


class DVLASensor(CoordinatorEntity[DVLACoordinator], SensorEntity):
    """Define an DVLA sensor."""

    def __init__(
        self,
        coordinator: DVLACoordinator,
        name: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{name}")},
            manufacturer=coordinator.data.get("make"),
            name=name.upper(),
            configuration_url="https://github.com/jampez77/DVLA-Vehicle-Checker/",
        )
        self._attr_unique_id = f"{DOMAIN}-{name}-{description.key}".lower()
        self.attrs: dict[str, Any] = {}
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get(self.entity_description.key, "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        for key in self.coordinator.data:
            self.attrs[key] = self.coordinator.data[key]
        return self.attrs


class DVLAEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity."""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self.entity_description.attr_fn(self)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""

        self.async_write_ha_state()
