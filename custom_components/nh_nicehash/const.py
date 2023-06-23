import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "nh_nicehash"
HOSTURL = "https://api2.nicehash.com"
UPDATE_INTERVAL = 60
Set_Rig_Status_SCHEMA = vol.Schema(
    {
        vol.Required('rigId'): cv.string,
        vol.Required('action'): cv.string,
    }
)

DEVICE_INFO = {
    "identifiers": {(DOMAIN, "nh_nicehash")},
    "name": "Nicehash",
    "manufacturer": "MorneSaunders360",
    "model": "Nicehash API",
    "sw_version": "1.0.6",
}