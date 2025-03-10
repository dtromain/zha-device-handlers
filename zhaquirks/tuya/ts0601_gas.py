"""Gas Sensor."""
import logging

import zigpy.profiles.zha
from zigpy.quirks import CustomCluster, CustomDevice
import zigpy.types as t
from zigpy.zcl.clusters.general import Basic, Groups, Ota, Scenes, Time
from zigpy.zcl.clusters.security import IasZone

from zhaquirks import Bus
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    ZONE_STATUS,
    ZONE_TYPE,
)

from . import TuyaManufCluster, TuyaManufClusterAttributes

_LOGGER = logging.getLogger(__name__)

TUYA_GAS_DETECTED_ATTR = 0x0401  # [0]/[1] [Detected]/[Clear]!


class TuyaGasDetectorCluster(TuyaManufClusterAttributes):
    """Manufacturer Specific Cluster of the TS0601 gas detector."""

    attributes = TuyaManufClusterAttributes.attributes.copy()
    attributes.update(
        {
            TUYA_GAS_DETECTED_ATTR: ("gas_detected", t.uint8_t, True),
        }
    )

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == TUYA_GAS_DETECTED_ATTR:
            if value == 0:
                self.endpoint.device.ias_bus.listener_event(
                    "update_zone_status", IasZone.ZoneStatus.Alarm_1
                )
            else:
                self.endpoint.device.ias_bus.listener_event("update_zone_status", 0)
        else:
            _LOGGER.warning(
                "[0x%04x:%s:0x%04x] unhandled attribute: 0x%04x",
                self.endpoint.device.nwk,
                self.endpoint.endpoint_id,
                self.cluster_id,
                attrid,
            )


class TuyaGasDetectorZone(CustomCluster, IasZone):
    """IAS Zone."""

    _CONSTANT_ATTRIBUTES = {ZONE_TYPE: IasZone.ZoneType.Carbon_Monoxide_Sensor}

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.ias_bus.add_listener(self)

    def update_zone_status(self, value):
        """Update IAS status."""
        super()._update_attribute(ZONE_STATUS, value)


class TuyaGasDetector0601(CustomDevice):
    """TS0601 _TZE200_ggev5fsl quirk."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.ias_bus = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        MODELS_INFO: [("_TZE200_ggev5fsl", "TS0601")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zigpy.profiles.zha.PROFILE_ID,
                DEVICE_TYPE: zigpy.profiles.zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaManufCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zigpy.profiles.zha.PROFILE_ID,
                DEVICE_TYPE: zigpy.profiles.zha.DeviceType.IAS_ZONE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaGasDetectorZone,
                    TuyaGasDetectorCluster,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            },
        },
    }
