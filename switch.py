from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.switch import SwitchEntity

import logging
import cc1101
import time
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=600)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType
) -> None:
  """Set up platform."""
  add_entities([HeaterSwitch()])

class HeaterSwitch(SwitchEntity):
  
  def __init__(self):
    self._attr_is_on = False
    self._attr_name = "Heater Control"
    self._attr_icon = "mdi:water-boiler"
    self.update()
    _LOGGER.info("Boiler initialised")

  def turn_on(self, **kwargs) -> None:
    self._attr_is_on = True
    
  def turn_off(self, **kwargs) -> None:
    self._attr_is_on = False

  def update(self) -> None:
    with cc1101.CC1101(lock_spi_device=True) as transceiver:
      transceiver.set_base_frequency_hertz(868.30e6)
      transceiver.set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
      transceiver.set_sync_word([0x9a,0xd3])
      transceiver.set_sync_mode(cc1101.SyncMode.TRANSMIT_16_MATCH_16_BITS)
      transceiver._set_modulation_format(cc1101.ModulationFormat.FSK2)
      transceiver.set_output_power([0xC0])
      
      transceiver._write_burst(cc1101.addresses.ConfigurationRegisterAddress.PKTCTRL1,[0x80])
      transceiver._write_burst(cc1101.addresses.ConfigurationRegisterAddress.PKTCTRL0,[0x04])
      transceiver._write_burst(cc1101.addresses.ConfigurationRegisterAddress.DEVIATN,[0x41]) 
      
      if self._attr_is_on:
        _LOGGER.info("HEATER ON")
        signal = b"\x11\x5F\xA3\x20\xA4\x08\x1E\x27\x00\x00\x3D\x00\x32\x93"
      else:
        _LOGGER.info("HEATER OFF")
        signal = b"\x11\x5F\xA3\x00\xA4\x08\x1E\x27\x00\x00\x3D\x00\x32\x73"
     
      transceiver.set_symbol_rate_baud(24100)
      transceiver.set_packet_length_bytes(14)
      transceiver.transmit(signal)
      time.sleep(0.5)
      transceiver.transmit(signal)
