import logging
import requests
import voluptuous as vol
from homeassistant import config_entries
import nicehash

DOMAIN = "nh_nicehash"

_LOGGER = logging.getLogger(__name__)

class NiceHashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        # Check if a configuration entry already exists. If so, abort the current flow.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}
        if user_input is not None:
            organisation_id = user_input.get("organisation_id")
            key = user_input.get("key")
            secret = user_input.get("secret")
            if not organisation_id or not key or not secret:
                errors["base"] = "empty_credentials"
            else:
                valid = await self._validate_credentials(organisation_id, key,secret)
                if valid:
                    return self.async_create_entry(title="NiceHash", data=user_input)
                else:
                    errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("organisation_id"): str,
                    vol.Required("key"): str,
                    vol.Required("secret"): str,
                }
            ),
            errors=errors,
        )


    async def _validate_credentials(self, organisation_id, key,secret):
        def check_credentials():
            validAuth = False
            try:
                host = 'https://api2.nicehash.com'
                private_api = nicehash.private_api(host, organisation_id, key, secret)
                json_response = private_api.get_accounts()
                if json_response == 401:
                    validAuth = True
                return validAuth
            except Exception as e:
                return validAuth

        return await self.hass.async_add_executor_job(check_credentials)

config_entries.HANDLERS.register(DOMAIN)(NiceHashConfigFlow)




