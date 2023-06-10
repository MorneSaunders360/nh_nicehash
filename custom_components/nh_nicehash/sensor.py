from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.sensor import SensorEntity
from functools import partial
from datetime import timedelta
import logging
import re
from .nicehash import private_api
import json
import aiohttp
import asyncio
# Constants
DOMAIN = "nh_nicehash"
_LOGGER = logging.getLogger(__name__)
DEVICE_INFO = {
    "identifiers": {(DOMAIN, "nh_nicehash")},
    "name": "Nicehash",
    "manufacturer": "MorneSaunders360",
    "model": "Nicehash API",
    "sw_version": "1.0.3",
}
UPDATE_INTERVAL = 60
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
    rig_device_pairs = []  # This needs to be populated with your (rigId, deviceId) pairs
    # Create sensor entities and add them
    entities = []
    for result_key in coordinator.data.keys():
        entity = NiceHashSensor(coordinator, result_key, device, coordinator.data.get('btcAddress'), config_entry)
        entities.append(entity)


    async_add_entities(entities)

class NiceHashSensor(SensorEntity):
    """Representation of a sensor entity for NiceHash data."""

    def __init__(self, coordinator, result_key, device, id, config_entry):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.result_key = result_key
        self.device = device
        self.id = id
        self.config_entry = config_entry

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
        if self.result_key == 'unpaidAmount_' + self.config_entry.data["currency"]:
            unpaid_amount_converted = self.coordinator.data[self.result_key]
            return round(unpaid_amount_converted, 2) if unpaid_amount_converted is not None else None
        else:
            return self.coordinator.data[self.result_key]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.result_key in ['unpaidAmount_' + self.config_entry.data["currency"], 'totalBalance_' + self.config_entry.data["currency"]]:
            return self.config_entry.data["currency"]
        else:
            return None

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
        elif "unpaidAmount" in self.result_key:
            return "monetary"
        elif "totalBalance" in self.result_key:
            return "monetary"
        elif "totalProfitability" in self.result_key:
            return "monetary"
        else:
            return None

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        # The keys from combined_data
        keys_combined_data = [
            'btcAddress',
            'totalProfitability',
            'totalRigs',
            'totalDevices',
            'totalProfitabilityLocal',
            'unpaidAmount',
            'unpaidAmount_' + self.config_entry.data["currency"],
            'totalBalance',
            'totalBalance_' + self.config_entry.data["currency"],
        ]
        # Prefixes from rigId and deviceId in combined_data
        prefixes_combined_data = [
            'maxTemp',
            'deviceName',
            'workerName',
            'minerStatus',
        ]
        # Check if result_key is in keys_combined_data or starts with a prefix from prefixes_combined_data
        if (self.result_key in keys_combined_data) or any(self.result_key.startswith(prefix) for prefix in prefixes_combined_data):
            return "measurement"
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
        currency = config_entry.data["currency"]
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
        # Fetch conversion rate from CoinConvert API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.coinconvert.net/convert/btc/{currency}?amount=1") as response:
                conversion_data = await response.json()
        
        
        conversion_rate = conversion_data[currency.upper()]
        totalBalance_converted = float(totalBalance) * conversion_rate if totalBalance else None
        unpaidAmount_converted = float(unpaidAmount) * conversion_rate if unpaidAmount else None
        combined_data = {
        'btcAddress': btcAddress,
        'totalProfitability': totalProfitability,
        'totalRigs': totalRigs,
        'totalDevices': totalDevices,
        'totalProfitabilityLocal': totalProfitabilityLocal,
        'unpaidAmount': unpaidAmount,
        'unpaidAmount_' + currency: round(unpaidAmount_converted, 2) if unpaidAmount_converted is not None else None,
        'totalBalance': totalBalance,
        'totalBalance_' + currency: round(totalBalance_converted, 2) if totalBalance_converted is not None else None
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
        raise UpdateFailed(f"Error fetching data from NiceHash API: {e}")