# Future Updates

Planned improvements and known limitations with notes on how to implement them.

---

## Sync `check_interval_hours` between HA and ESPHome automatically

### Current state

`check_interval_hours` is configured in two places that must be kept manually in sync:

- ESPHome substitution in `config_examples/seeede1002.yaml` (and `_rocky.yaml`):
  ```yaml
  substitutions:
    check_interval_hours: "24"
  ```
- Blueprint input in `blueprints/automation/forecats/forecats.yaml`:
  ```yaml
  input:
    check_interval_hours:
      default: 24
  ```

If you change the interval in one place, you must update the other and reflash the ESP.

### Goal

Configure the interval once in HA and have both the automation and the ESP device
read from it automatically — no reflash needed.

### How to implement

**Step 1 — Add a `number` platform entity to the forecats integration**

Create `custom_components/forecats/number.py`:

```python
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime

from .const import DOMAIN  # add DOMAIN = "forecats" to a const.py

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([ForecastsCheckIntervalNumber()])


class ForecastsCheckIntervalNumber(NumberEntity):
    _attr_name = "Forecats Check Interval"
    _attr_unique_id = "forecats_check_interval"
    _attr_native_min_value = 1
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_value = 24
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:clock-outline"

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
```

This also requires:
- Adding `"number"` to `PLATFORMS` list in `__init__.py`
- Setting up `async_setup_entry` in `__init__.py` (currently the integration uses
  `async_setup`, not config entries — this would require migrating to a config flow)
- Adding `const.py` with `DOMAIN = "forecats"`

**Step 2 — Update the blueprint to read from the entity**

Remove the `check_interval_hours` input and replace with a variable:

```yaml
variables:
  check_interval_hours_var: "{{ states('number.forecats_check_interval') | int(24) }}"
```

**Step 3 — Update ESPHome to read from the entity**

Remove the `check_interval_hours` substitution and add a sensor:

```yaml
sensor:
  - platform: homeassistant
    entity_id: number.forecats_check_interval
    id: ha_check_interval
    internal: true
```

Add a `wait_until` in the boot sequence after the time sync wait:

```yaml
- wait_until:
    condition:
      lambda: 'return id(ha_check_interval).has_state();'
    timeout: 15s
```

Replace `${check_interval_hours}` in the sleep duration lambda with:

```cpp
int interval_hours = id(ha_check_interval).has_state()
  ? (int)id(ha_check_interval).state
  : 24;  // fallback if HA not connected
int interval_minutes = interval_hours * 60;
```

### References

- ESPHome `homeassistant` sensor platform:
  https://esphome.io/components/sensor/homeassistant.html
- HA `number` entity platform developer docs:
  https://developers.home-assistant.io/docs/core/entity/number/
- Community thread on passing HA values to ESPHome:
  https://community.home-assistant.io/t/how-to-pass-a-variable-from-home-assistant-front-end-to-esphome/183845
