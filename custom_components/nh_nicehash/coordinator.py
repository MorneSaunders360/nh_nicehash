import logging
import json
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from functools import partial
from datetime import timedelta
from .const import UPDATE_INTERVAL,HOSTURL
from .nicehash import private_api
from functools import partial
_LOGGER = logging.getLogger(__name__)
async def async_get_coordinator(hass, config_entry):
    """Set up the DataUpdateCoordinator."""
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Sunsynk",
        update_method=partial(fetch_data, config_entry,hass),
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )
    return coordinator

async def fetch_data(config_entry, hass):
    try:
        host = HOSTURL
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
        devicesStatuses = data['devicesStatuses']
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
        'devicesStatuses': list(devicesStatuses.keys())[0],
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
            combined_data[f'{rigId}'] = rigId
            combined_data[f'{rigId}_workerName'] = workerName
            combined_data[f'{rigId}_minerStatus'] = minerStatus

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



        return combined_data

    except Exception as e:
        _LOGGER.error("Error fetching data from NiceHash API: %s", e)
        raise UpdateFailed(f"Error fetching data from NiceHash API: {e}")

