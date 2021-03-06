"""
Firmware   | LAN type  | uiid | Product Model
-----------|-----------|------|--------------
ITA-GZ1-GL | plug      | 14   | Sonoff (Sonoff Basic)
PSF-B01-GL | plug      | 1    | - (switch 1ch)
PSF-BD1-GL | plug      | 1    | MINI (Sonoff Mini)
PSF-B04-GL | strip     | 2    | - (switch 2ch)
PSF-B04-GL | strip     | 4    | 4CHPRO (Sonoff 4CH Pro)
"""
import logging
from typing import Optional

from homeassistant.helpers.entity import ToggleEntity

# noinspection PyUnresolvedReferences
from . import DOMAIN, CONF_FORCE_UPDATE, SCAN_INTERVAL
from .sonoff_main import EWeLinkDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_entities,
                               discovery_info=None):
    if discovery_info is None:
        return

    deviceid = discovery_info['deviceid']
    channels = discovery_info['channels']
    registry = hass.data[DOMAIN]
    add_entities([EWeLinkToggle(registry, deviceid, channels)])


class EWeLinkToggle(ToggleEntity, EWeLinkDevice):
    _should_poll = None

    async def async_added_to_hass(self) -> None:
        device = self._init()
        self._should_poll = device.pop(CONF_FORCE_UPDATE, False)

    def _update_handler(self, state: dict, attrs: dict):
        # TH bug in local mode https://github.com/AlexxIT/SonoffLAN/issues/110
        if not (self._is_th_3_4_0 and attrs.get('temperature') == 0 and
                attrs.get('humidity') == 0):
            self._attrs.update(attrs)

        if 'switch' in state or 'switches' in state:
            self._is_on = any(self._is_on_list(state))

        self.schedule_update_ha_state()

    @property
    def should_poll(self) -> bool:
        # The device itself sends an update of its status
        return self._should_poll

    @property
    def unique_id(self) -> Optional[str]:
        if self.channels:
            chid = ''.join(str(ch) for ch in self.channels)
            return f'{self.deviceid}_{chid}'
        else:
            return self.deviceid

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def state_attributes(self):
        return self._attrs

    @property
    def available(self) -> bool:
        device: dict = self.registry.devices[self.deviceid]
        return device['available']

    @property
    def supported_features(self):
        return 0

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self._turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        await self._turn_off()

    async def async_update(self):
        """Auto refresh device state.

        Called from: `EntityPlatform._update_entity_states`

        https://github.com/AlexxIT/SonoffLAN/issues/14
        """
        _LOGGER.debug(f"Refresh device state {self.deviceid}")

        if self._is_on:
            await self.async_turn_on()
        else:
            await self.async_turn_off()
