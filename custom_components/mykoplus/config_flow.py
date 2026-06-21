from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import MykoPlusClient
from .api.exceptions import MykoPlusAuthError, MykoPlusError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
USER_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str})

class MykoPlusConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            client = MykoPlusClient(user_input[CONF_EMAIL], user_input[CONF_PASSWORD], session=async_get_clientsession(self.hass))
            try:
                await client.login()
            except MykoPlusAuthError:
                errors['base'] = 'invalid_auth'
            except MykoPlusError:
                errors['base'] = 'cannot_connect'
            else:
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)
        return self.async_show_form(step_id='user', data_schema=USER_SCHEMA, errors=errors)
