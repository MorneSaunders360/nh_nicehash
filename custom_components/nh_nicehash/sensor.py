from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN,DEVICE_INFO
from .coordinator import async_get_coordinator
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors from config entry."""
    # Create the data update coordinator
    coordinator = await async_get_coordinator(hass, config_entry)
    
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
    device_info = DEVICE_INFO.copy()
    device_infos = DEVICE_INFO.copy()
    for result_key in coordinator.data.keys():
        if "miningRig_" in result_key:
            device_info["identifiers"] = {(DOMAIN, "miningRig_" + coordinator.data[result_key]["rigId"])}
            device_info["name"] = coordinator.data[result_key]["workerName"]
            device_rig = device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                **device_info,
            )
            for result_keys in coordinator.data[result_key].keys():
                if result_keys not in ['workerName']:
                    entity = NiceHashSensorRig(coordinator, result_keys, device_rig, "miningRig_" + coordinator.data[result_key]["rigId"],config_entry)
                    entities.append(entity)
        elif "miningRigDevice_" in result_key:
            device_infos["identifiers"] = {(DOMAIN, "miningRigDevice_" + coordinator.data[result_key]["deviceId"])}
            device_infos["name"] = coordinator.data[result_key]["deviceName"]
            device_rig_device = device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                **device_infos,
            )
            for result_keys in coordinator.data[result_key].keys():
                if result_keys not in ['deviceName','deviceId']:
                    entity = NiceHashSensorRigDevice(coordinator, result_keys, device_rig_device, "miningRigDevice_" + coordinator.data[result_key]["deviceId"])
                    entities.append(entity)
        else:
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
        return f"{self.device.name} {self.result_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device.name} {self.result_key}"

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
        if "unpaidAmount" in self.result_key:
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
        if "unpaidAmount" in self.result_key:
            return "measurement"
        elif "totalBalance" in self.result_key:
            return "measurement"
        elif "totalProfitability" in self.result_key:
            return "measurement"
        else:
            return None

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
class NiceHashSensorRig(SensorEntity):
    """Representation of a sensor entity for NiceHash data."""

    def __init__(self, coordinator, result_key, device, id,config_entry):
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
            "identifiers": {(DOMAIN, self.id)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.sw_version,
            "via_device": (DOMAIN, self.device.id),
        }

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.name} {self.result_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device.name} {self.result_key}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.id][self.result_key]
            

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
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
        else:
            return None

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        if "maxTemp" in self.result_key:
            return "measurement"
        elif "Temperature" in self.result_key:
            return "measurement"
        elif "voltage" in self.result_key:
            return "measurement"
        elif "Memory" in self.result_key:
            return "measurement"
        elif "Power usage" in self.result_key:
            return "measurement"
        elif "Power Limit" in self.result_key:
            return "measurement"
        elif "clock" in self.result_key:
            return "measurement"
        elif "speed" in self.result_key:
            return "measurement"
        elif "Load" in self.result_key:
            return "measurement"
        else:
            return None


    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
class NiceHashSensorRigDevice(SensorEntity):
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
            "identifiers": {(DOMAIN, self.id)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.sw_version,
            "via_device": (DOMAIN, self.device.id),
        }

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.name} {self.result_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device.name} {self.result_key}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self.id][self.result_key]
            

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
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
        else:
            return None

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        if "maxTemp" in self.result_key:
            return "measurement"
        elif "Temperature" in self.result_key:
            return "measurement"
        elif "voltage" in self.result_key:
            return "measurement"
        elif "Memory" in self.result_key:
            return "measurement"
        elif "Power usage" in self.result_key:
            return "measurement"
        elif "Power Limit" in self.result_key:
            return "measurement"
        elif "clock" in self.result_key:
            return "measurement"
        elif "speed" in self.result_key:
            return "measurement"
        elif "Load" in self.result_key:
            return "measurement"
        else:
            return None

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()