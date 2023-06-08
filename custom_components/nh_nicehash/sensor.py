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
    """Representation of a sensor entity for NiceHash data."""

    def __init__(self, coordinator, result_key, device, id):
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
        return f"nicehash_{self.id}_{self.result_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"nicehash_{self.id}_{self.result_key}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.result_key]

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if "maxTemp" in self.result_key:
            return "temperature"
        elif "Temperature" in self.result_key:
            return "temperature"
        elif "voltage" in self.result_key:
            return "voltage"
        elif "Memory" in self.result_key:
            return "frequency"
        elif "Power usage" in self.result_key:
            return "power"
        elif "Power Limit" in self.result_key:
            return "power_factor"
        elif "clock" in self.result_key:
            return "frequency"
        elif "speed" in self.result_key:
            return "power_factor"
        elif "Load" in self.result_key:
            return "power_factor"
        elif self.result_key == "totalProfitability":
            return "monetary"
        elif self.result_key in ["unpaidAmount", "totalBalance"]:
            return "monetary"
        else:
            return None


    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

async def fetch_data(config_entry, hass):
    try:
        host = 'https://api2.nicehash.com'
        organisation_id = config_entry.data["organisation_id"]
        key = config_entry.data["key"]
        secret = config_entry.data["secret"]
        api_instance = private_api(host, organisation_id, key, secret, hass, False)

        rigsResponse = await api_instance.get_rigs()
        my_accounts = await api_instance.get_accounts_for_currency("BTC")

        rigsResponse_json = json.dumps(rigsResponse)
        my_accounts_json = json.dumps(my_accounts)

        data = json.loads(rigsResponse_json)
        totalBalance = json.loads(my_accounts_json)['totalBalance']

        btcAddress = data['btcAddress']
        totalProfitability = data['totalProfitability']
        totalRigs = data['totalRigs']
        totalDevices = data['totalDevices']
        totalProfitabilityLocal = data['totalProfitabilityLocal']
        unpaidAmount = data['unpaidAmount']

        combined_data = {
            'btcAddress': btcAddress,
            'totalProfitability': totalProfitability,
            'totalRigs': totalRigs,
            'totalDevices': totalDevices,
            'totalProfitabilityLocal': totalProfitabilityLocal,
            'unpaidAmount': unpaidAmount,
            'totalBalance': totalBalance
        }

        # Loop over each mining rig and fetch additional data
        for item in data['miningRigs']:
            rigId = item['rigId']
            workerName = item['v4']['mmv']['workerName']
            minerStatus = item['minerStatus']

            # Find the maximum temperature across all devices in the rig
            temps = [int(device['odv'][0]['value']) for device in item['v4']['devices']]
            max_temp = max(temps)
            combined_data[f'{rigId}_maxTemp'] = max_temp

            # Add device information to the combined_data dictionary
            for device in item['v4']['devices']:
                deviceId = device['dsv']['id']
                deviceName = device['dsv']['name']
                combined_data[f'{rigId}_{deviceId}_deviceName'] = deviceName

                # Add odv data to the combined_data dictionary
                for odv_item in device['odv']:
                    key = odv_item['key']
                    if key not in ['ELP profile','ELP profile ID','Fan profile','Fan profile ID','OC profile ID','OC profile']:
                        value = odv_item['value']
                        unit = odv_item['unit']
                        combined_data[f'{rigId}_{deviceId}_{key}'] = f'{value} {unit}'


            combined_data[f'{rigId}'] = rigId
            combined_data[f'{rigId}_workerName'] = workerName
            combined_data[f'{rigId}_minerStatus'] = minerStatus

        return combined_data

    except Exception as e:
        _LOGGER.error("Error fetching data from NiceHash API: %s", e)
        return None