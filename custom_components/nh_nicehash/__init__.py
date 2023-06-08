from homeassistant import config_entries, core
from .nicehash import private_api
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
DOMAIN = "nh_nicehash"
Set_Rig_Status_SCHEMA = vol.Schema(
    {
        vol.Required('rigId'): cv.string,
        vol.Required('action'): cv.string,
    }
)
async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry):
    host = 'https://api2.nicehash.com'
    organisation_id = entry.data["organisation_id"]
    key = entry.data["key"]
    secret = entry.data["secret"]
    api_instance = private_api(host, organisation_id, key, secret, hass, False)

    async def set_rig_status_handler(call):
        await api_instance.set_rig_status(call.data.get('rigId'),call.data.get('action'))

    hass.services.async_register(
        DOMAIN, 'setrigstatus', set_rig_status_handler, Set_Rig_Status_SCHEMA)
    
    return await hass.async_add_executor_job(setup, hass, entry)

def setup(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    # Return boolean to indicate that initialization was successful.
    return True

