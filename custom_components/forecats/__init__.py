import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .forecats import generate_pet_pic
from .models import GenerateRequest

_LOGGER = logging.getLogger(__name__)

PET_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("description"): cv.string,
        vol.Optional("type", default="cat"): cv.string,
    }
)

# Fields marked Optional fall back to values stored in the config entry.
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("gemini_api_key"): cv.string,
        vol.Optional("location"): cv.string,
        vol.Required("forecast"): dict,
        vol.Required("temperature_unit"): cv.string,
        vol.Required("pets"): [PET_SCHEMA],
        vol.Optional("input_image_paths", default=[]): [cv.string],
<<<<<<< HEAD
        vol.Optional("input_image_dir"): vol.Any(cv.string, None),
        vol.Required("art_styles"): [cv.string],
        vol.Optional("image_gen_aspect_ratio"): cv.string,
        vol.Optional("image_gen_resolution"): cv.string,
        vol.Optional("final_image_size"): cv.string,
        vol.Optional("display_profile"): vol.Any(cv.string, None),
        vol.Optional("archive_dir", default="/media/forecats"): cv.string,
    },
)


def _build_request(call_data: dict, stored: dict) -> GenerateRequest:
    """Merge service call data with stored config entry defaults."""

    def get(key, required=False):
        val = call_data.get(key) or stored.get(key)
        if required and not val:
            raise HomeAssistantError(
                f"'{key}' was not provided in the service call and is not set in the Forecats config entry."
            )
        return val

    return GenerateRequest(
        gemini_api_key=get("gemini_api_key", required=True),
        location=get("location", required=True),
        forecast=call_data["forecast"],
        temperature_unit=call_data["temperature_unit"],
        pets=call_data["pets"],
        input_image_paths=call_data.get("input_image_paths") or [],
        input_image_dir=get("input_image_dir"),
        art_styles=call_data["art_styles"],
        image_gen_aspect_ratio=get("image_gen_aspect_ratio", required=True),
        image_gen_resolution=get("image_gen_resolution", required=True),
        final_image_size=get("final_image_size", required=True),
        display_profile=get("display_profile"),
        archive_dir=get("archive_dir") or "/media/forecats",
    )


def _register_service(hass: HomeAssistant) -> None:
    """Register the generate_pet_picture service (idempotent)."""
    if hass.services.has_service(DOMAIN, "generate_pet_picture"):
        return

    async def handle_generate(call: ServiceCall) -> None:
        stored = hass.data.get(DOMAIN, {})
        try:
            data = _build_request(dict(call.data), stored)
        except Exception as err:
            _LOGGER.error("Invalid service call data: %s", err)
            raise

        _LOGGER.info("Received generate_pet_picture service call with data: %s", data)
        try:
            original_path, optimized_path = await hass.async_add_executor_job(
                generate_pet_pic,
                data,
                hass.config.path(),
            )
            _LOGGER.info("Generated pet pictures: %s, %s", original_path, optimized_path)
        except Exception:
            _LOGGER.exception("Failed to generate pet picture")

    hass.services.async_register(DOMAIN, "generate_pet_picture", handle_generate, SERVICE_SCHEMA)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up via configuration.yaml (legacy / YAML path)."""
    hass.data.setdefault(DOMAIN, {})
    _register_service(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Forecats from a config entry (UI path)."""
    # Merge initial data with any options saved later
    hass.data[DOMAIN] = {**entry.data, **entry.options}
    _register_service(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options are changed so hass.data stays in sync."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data.pop(DOMAIN, None)
    hass.services.async_remove(DOMAIN, "generate_pet_picture")
    return True
