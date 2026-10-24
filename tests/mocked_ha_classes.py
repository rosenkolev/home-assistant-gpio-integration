"""Home Assistant mocks; must not import the integration package."""


class MockedBaseEntity:
    ha_state_update_scheduled = False
    ha_state_update_scheduled_force_refresh = False
    ha_state_write = False
    ha_added_to_hass = False
    hass = 1

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    def async_write_ha_state(self):
        self.ha_state_write = True

    def async_schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = force_refresh

    def schedule_update_ha_state(self, force_refresh=False):
        self.ha_state_update_scheduled = True
        self.ha_state_update_scheduled_force_refresh = False

    async def async_added_to_hass(self) -> None:
        self.ha_added_to_hass = True

    def async_on_remove(self, _=None):
        pass

    async def async_will_remove_from_hass(self) -> None:
        pass


class MockedOptionsFlow:
    step_id: str
    data_schema: str
    abort_reason: str
    errors: str
    unique_id: str
    entity_title: str
    entity_data: dict

    def async_show_form(self, step_id: str, data_schema: dict, errors: dict = None):
        self.step_id = step_id
        self.data_schema = data_schema
        self.errors = errors

    def async_abort(self, reason: str):
        self.abort_reason = reason

    async def async_set_unique_id(self, unique_id: str):
        self.unique_id = unique_id

    def async_create_entry(self, title: str, data: dict):
        self.entity_title = title
        self.entity_data = data


class MockedConfigFlow(MockedOptionsFlow):
    @classmethod
    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)


class MockVolSchema:
    def __init__(self, schema, extra=None):
        self.schema = schema


class MockColOptional:
    def __init__(self, name, default=None, description=None):
        self.schema = name
        self.default = lambda: default


class MockedPlatform:
    SWITCH = "switch"
    LIGHT = "light"
    COVER = "cover"
    BINARY_SENSOR = "binary_sensor"
    FAN = "fan"
    SENSOR = "sensor"
    NUMBER = "number"


class MockedDeviceInfo:
    def __init__(self, identifiers, name, manufacturer, model, sw_version):
        self.identifiers = identifiers
        self.name = name
        self.manufacturer = manufacturer
        self.model = model
        self.sw_version = sw_version
