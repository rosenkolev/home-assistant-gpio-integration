import pytest

from custom_components.gpio_integration.config_flow import (
    ConfigFlow,
    fill_schema_missing_values,
)
from custom_components.gpio_integration.schemas.main import MAIN_SCHEMA, EntityTypes


def test__fill_schema_missing_values():
    config = dict(
        {
            "CONF_NAME": "Test",
            "CONF_PORT": 1,
        },
    )

    fill_schema_missing_values(EntityTypes.SWITCH, config)
    assert config.get("invert_logic") is False
    assert config.get("default_state") is False


@pytest.mark.asyncio
async def test__config_flow_no_type():
    config = ConfigFlow()
    await config.async_step_user()
    assert config.step_id == "user"
    assert config.data_schema == MAIN_SCHEMA


@pytest.mark.asyncio
async def test__config_flow():
    config = ConfigFlow()
    await config.async_step_user(dict(type="Switch"))
    assert config.step_id == "common_setup"
