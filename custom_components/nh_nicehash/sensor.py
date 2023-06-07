from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.sensor import SensorEntity
from functools import partial
from datetime import timedelta
import logging
import re
from .nicehash import private_api
import json
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
        update_method=partial(fetch_data, config_entry,hass),
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
        entity = NiceHashSensor(coordinator, result_key,device,coordinator.data.get('btcAddress'))
        entities.append(entity)

    async_add_entities(entities)


class NiceHashSensor(SensorEntity):
    """Representation of a sensor entity for Solar Sunsynk data."""
    def __init__(self, coordinator, result_key,device,id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.result_key = result_key
        self.device = device 
        self.id = id
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "nh_nicehash")},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.sw_version,
            "via_device": (DOMAIN, self.device.id),
        }
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"nicehash_{self.result_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"nicehash_{self.id}_{self.result_key}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.result_key]

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()


async def fetch_data(config_entry, hass):
    host = 'https://api2.nicehash.com'
    organisation_id = config_entry.data["organisation_id"]
    key = config_entry.data["key"]
    secret = config_entry.data["secret"]
    api_instance = private_api(host, organisation_id, key, secret, hass, False)
    rigsResponse = await api_instance.get_rigs()
    user = json.dumps(rigsResponse)
    data = json.loads(user)
    # Retrieve and format data
    btcAddress = data['btcAddress']
    totalProfitability = data['totalProfitability']
    totalRigs = data['totalRigs']
    totalDevices = data['totalDevices']
    totalProfitabilityLocal = data['totalProfitabilityLocal']

    combined_data = {
        'btcAddress': btcAddress,
        'totalProfitability': totalProfitability,
        'totalRigs': totalRigs,
        'totalDevices': totalDevices,
        'totalProfitabilityLocal': totalProfitabilityLocal,
    }

    # Loop over each mining rig and fetch additional data
    for item in data['miningRigs']:
        rigId = item['rigId']
        workerName = item['v4']['mmv']['workerName']
        minerStatus = item['minerStatus']

        # Update the combined_data dictionary with separate entities
        combined_data[f'{rigId}_workerName'] = workerName
        combined_data[f'{rigId}_minerStatus'] = minerStatus

    return combined_data






