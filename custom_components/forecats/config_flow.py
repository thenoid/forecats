"""Config flow for Forecats."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN

ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]
RESOLUTIONS = ["1K", "2K", "4K"]
DISPLAY_PROFILES = [
    SelectOptionDict(value="", label="None (original colors)"),
    SelectOptionDict(value="spectra6", label="Spectra 6 (e-ink)"),
]

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("gemini_api_key"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required("location"): TextSelector(),
        vol.Optional("input_image_dir", default=""): TextSelector(),
    }
)

STEP_DISPLAY_SCHEMA = vol.Schema(
    {
        vol.Optional("image_gen_aspect_ratio", default="16:9"): SelectSelector(
            SelectSelectorConfig(options=ASPECT_RATIOS, mode=SelectSelectorMode.DROPDOWN)
        ),
        vol.Optional("image_gen_resolution", default="1K"): SelectSelector(
            SelectSelectorConfig(options=RESOLUTIONS, mode=SelectSelectorMode.DROPDOWN)
        ),
        vol.Optional("final_image_size", default="800x480"): TextSelector(),
        vol.Optional("display_profile", default=""): SelectSelector(
            SelectSelectorConfig(options=DISPLAY_PROFILES, mode=SelectSelectorMode.DROPDOWN)
        ),
    }
)


class ForecatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Forecats."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            if not self._data.get("input_image_dir"):
                self._data["input_image_dir"] = None
            return await self.async_step_display()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

    async def async_step_display(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            if not self._data.get("display_profile"):
                self._data["display_profile"] = None
            return self.async_create_entry(
                title=f"Forecats ({self._data['location']})",
                data=self._data,
            )

        return self.async_show_form(step_id="display", data_schema=STEP_DISPLAY_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ForecatsOptionsFlow(config_entry)


class ForecatsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for reconfiguring Forecats."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if not user_input.get("input_image_dir"):
                user_input["input_image_dir"] = None
            if not user_input.get("display_profile"):
                user_input["display_profile"] = None
            return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Required("gemini_api_key", default=current.get("gemini_api_key", "")): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required("location", default=current.get("location", "")): TextSelector(),
                vol.Optional("input_image_dir", default=current.get("input_image_dir") or ""): TextSelector(),
                vol.Optional("image_gen_aspect_ratio", default=current.get("image_gen_aspect_ratio", "16:9")): SelectSelector(
                    SelectSelectorConfig(options=ASPECT_RATIOS, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional("image_gen_resolution", default=current.get("image_gen_resolution", "1K")): SelectSelector(
                    SelectSelectorConfig(options=RESOLUTIONS, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional("final_image_size", default=current.get("final_image_size", "800x480")): TextSelector(),
                vol.Optional("display_profile", default=current.get("display_profile") or ""): SelectSelector(
                    SelectSelectorConfig(options=DISPLAY_PROFILES, mode=SelectSelectorMode.DROPDOWN)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
