from custom_components.gpio_integration.config_flow import fill_schema_missing_values
from custom_components.gpio_integration.schemas.main import EntityTypes


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
