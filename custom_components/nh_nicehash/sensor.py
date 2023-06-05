from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.sensor import SensorEntity
from functools import partial
from datetime import timedelta
import aiohttp
import async_timeout
import json
import logging
import time
import re
import nicehash
# Constants
DOMAIN = "nh_nicehash"
_LOGGER = logging.getLogger(__name__)
DEVICE_INFO = {
    "identifiers": {(DOMAIN, "nh_nicehash")},
    "name": "Nicehash",
    "manufacturer": "MorneSaunders360",
    "model": "Nicehash API",
    "sw_version": "1.0",
}
UPDATE_INTERVAL = 10
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors from config entry."""
    # Create the data update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=partial(fetch_data, config_entry),
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    # Create device registry
    device_registry = hass.helpers.device_registry.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        **DEVICE_INFO,
    )

    # Create sensor entities and add them
    entities = []
    for result_key in coordinator.data.keys():
        entity = SolarSunSynkSensor(coordinator, result_key,device)
        entities.append(entity)

    async_add_entities(entities)


class SolarSunSynkSensor(SensorEntity):
    """Representation of a sensor entity for Solar Sunsynk data."""
    def __init__(self, coordinator, result_key,device):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.result_key = result_key
        self.device = device 
    
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "solar_sunsynk")},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.sw_version,
            "via_device": (DOMAIN, self.device.id),
        }
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"sunsynk_{self.result_key}"



    @property
    def name(self):
        """Return the name of the sensor."""
        return self._format_key_to_title(self.result_key)

    def _format_key_to_title(self, key):
        """Format the key in the format 'totalPower' to 'Total Power'."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).title()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.result_key]

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

async def fetch_data(session, config_entry):
    host = 'https://api2.nicehash.com'
    organisation_id =config_entry.data["organisation_id"]
    key = config_entry.data["key"]
    secret = config_entry.data["secret"]
    private_api = nicehash.private_api(host, organisation_id, key, secret)
    rigs = private_api.get_rigs()
    # Combine all the plant data into a single dictionary
    combined_data = {}
    for info in rigs:
        info = {k: str(v)[:255] for k, v in info.items()}
        combined_data.update(info)
            
    return combined_data
