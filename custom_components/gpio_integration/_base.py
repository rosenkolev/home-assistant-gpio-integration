import datetime

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN, get_logger

_LOGGER = get_logger()


class ClosableMixin:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self._close()

    def _close(self) -> None:
        if hasattr(self, "_io") and self._io is not None:
            self._io.close()
            self._io = None


class ReprMixin:
    def __repr__(self) -> str:
        if hasattr(self, "_attr_name"):
            return f"{self._io!r} ({self._attr_name})"

        return f"{self._io!r} ({self.__class__.__name__})"


class DeviceMixin:
    def _get_device_id(self) -> str:
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._get_device_id())},
            name=self._attr_name,
            manufacturer="Raspberry Pi",
            model="GPIO",
            sw_version="1",
        )


class AutoUpdMixin:
    @property
    def should_auto_update_state(self) -> bool:
        pass

    def enable_state_auto_update(self, interval_sec: int) -> None:
        _LOGGER.debug(f"{self._io!s} auto-update activated")
        timer_cancel = async_track_time_interval(
            self.hass,
            self._auto_update_callback,
            datetime.timedelta(seconds=interval_sec),
            cancel_on_shutdown=True,
        )

        self.async_on_remove(timer_cancel)

    def _auto_update_callback(self, _=None):
        if self.should_auto_update_state:
            _LOGGER.debug(f"{self._io!s} auto-update scheduled")
            self.schedule_update_ha_state(force_refresh=True)
