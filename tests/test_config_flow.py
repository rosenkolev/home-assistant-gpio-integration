import pytest

from custom_components.gpio_integration.config_flow import (
    ConfigFlow,
    fill_schema_missing_values,
)
from custom_components.gpio_integration.schemas.light import LIGHT_VARIATION_SCHEMA
from custom_components.gpio_integration.schemas.main import MAIN_SCHEMA, EntityTypes
from custom_components.gpio_integration.schemas.switch import SWITCH_SCHEMA


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
async def test__config_flow_common():
    config = ConfigFlow()
    await config.async_step_user(dict(type="Switch"))
    assert config.step_id == "common_setup"
    assert config.data_schema == SWITCH_SCHEMA


@pytest.mark.asyncio
async def test__config_flow_variation():
    config = ConfigFlow()
    await config.async_step_user(dict(type="Light"))
    assert config.step_id == "select_variation"
    assert config.data_schema == LIGHT_VARIATION_SCHEMA


@pytest.mark.asyncio
async def test__config_flow_type_check():
    config = ConfigFlow()
    await config.async_step_common_setup()
    assert config.abort_reason == "unknown_type"

    config.type = None
    await config.async_step_common_setup()
    assert config.abort_reason == "unknown_type"


@pytest.mark.asyncio
async def test__config_common_setup_reshow_form():
    config = ConfigFlow()
    config.type = "switch"
    await config.async_step_common_setup()
    assert config.step_id == "common_setup"
    assert config.data_schema == SWITCH_SCHEMA


@pytest.mark.asyncio
async def test__config_flow_common_setup_check_fail():
    config = ConfigFlow()
    config.type = "switch"
    await config.async_step_common_setup(dict(type="switch", CONF_NAME=""))
    assert config.errors["base"] == "Name is required"


@pytest.mark.asyncio
async def test__config_flow_common_setup():
    config = ConfigFlow()
    config.type = "switch"
    await config.async_step_common_setup(
        dict(type="switch", CONF_NAME="Test name", CONF_PORT=20)
    )
    assert config.unique_id == "test_name"
    assert config.entity_title == "Test name"
    assert config.entity_data["type"] == "switch"
    assert config.entity_data["CONF_NAME"] == "Test name"
    assert config.entity_data["CONF_PORT"] == 20
