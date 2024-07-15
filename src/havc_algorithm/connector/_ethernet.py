"""Read from / Write to PLC."""

import logging
import time
from datetime import datetime

from pycomm3 import LogixDriver
from pydantic import BaseModel

from ..base import BaseConnector
from ..data import ControlData, Setting, StationData


class StationTags(BaseModel):
    """
    Tagname must be unique
    Pumping station measurement
    The attributes of StationTags should match StationData
    """

    # water_level: str = "plc.water_level"
    # switch: list[str] = [f"plc.pump_state[{i}].run" for i in range(8)]
    # speed: list[str] = [f"plc.pump_state[{i}].speed" for i in range(8)]
    # outflow: list[str] = [f"plc.pump_state[{i}].flow" for i in range(8)]
    # sec: list[str] = [f"plc.pump_state[{i}].sec" for i in range(8)]
    # # tag_return_temperatue: str = 'plc.return_temperatue' #TODO: check with onsite plc tag
    # TT_CWS_1: float = 'TT_CWR_1'
    # TT_CWR_1: float = 'TT_CWR_1'
    Tag_INT: int = 'Tag_INT'
    Tag_TW: float = 'Tag_TW'
    Tag_CTW_SP: float = 'Tag_CTW_SP'


class ControlTags(BaseModel):
    """
    Tagname must be unique
    Control commands for pumps
    The attributes of ControlTags should match ControlData
    """

    # TODO: use timestamp to restore inflow
    timestamp: str = "ai_output.inflow"
    switch: list[str] = [f"ai_output.pump[{i}].control.run" for i in range(8)]
    # speed: list[str] = [f"ai_output.pump[{i}].control.speed" for i in range(8)]
    total_outflow_setpoint: str = "ai_output.setpoint"


class SettingTags(BaseModel):
    """
    Tagname must be unique
    Settings for AutoFlow
    """

    outflow_lower: str = "ai_input.controller.speed.level_flow.flow_lower"
    outflow_upper: str = "ai_input.controller.speed.level_flow.flow_upper"
    h_setpoint: str = "ai_input.controller.speed.level_flow.level_setpoint"
    pid_kp: str = "ai_input.controller.speed.level_flow.level_lower"
    pid_ki: str = "ai_input.controller.speed.level_flow.level_upper"
    pid_kb: str = "ai_input.controller.speed.flow.level_upper"

class HvacTags(BaseModel):
    """
    Tagname must be unique
    Settings for AutoFlow
    """
    Tag_INT: int = 'Tag_INT'
    Tag_TW: float = 'Tag_TW'
    Tag_CTW_SP: float = 'Tag_CTW_SP'

class Tags(BaseModel):
    """
    Tagname must be unique
    Store all tags
    """

    station: StationTags = StationTags()
    control: ControlTags = ControlTags()
    setting: SettingTags = SettingTags()
    hvac: HvacTags = HvacTags()


class EthernetConnector(BaseConnector):
    """Read from or write to PLC tags."""

    def __init__(self, sample_time: float, path: str, **kwargs):
        super().__init__(sample_time=sample_time, path=path, **kwargs)

    def _read(self, tags: str | list[str]):
        with LogixDriver(getattr(self, "path")) as plc:
            if isinstance(tags, str):
                return plc.read(tags).value
            return [x.value for x in plc.read(*tags)]

    def _write(self, tags: str | list[str], values):
        with LogixDriver(getattr(self, "path")) as plc:
            if isinstance(tags, str):
                return plc.write((tags, values))
            tags_values = zip(tags, values)
            return plc.write(*tags_values)

    def _write_data(self, tags: BaseModel, data: BaseModel):
        """Write data to PLC"""
        if set(tags.model_fields.keys()) > set(data.model_fields.keys()):
            msg = "The attributes of tags and data are not match."
            logging.error(msg)
            raise AttributeError(msg)
        for name in tags.model_fields:
            tag_str = getattr(tags, name)
            self._write(tag_str, getattr(data, name))

    def write_output(self, data: ControlData):
        """Write control data to PLC"""
        self._write_data(Tags().control, data)

    def write_input(self, data: StationData):
        """Used for testing/virtual pumping station."""
        self._write_data(Tags().station, data)

    def write_setting(self, data: Setting):
        """Used for testing/virtual pumping station."""
        self._write_data(Tags().setting, data)

    def read_output(self):
        """Used for testing/virtual pumping station."""
        plc_tags = Tags().control
        data_dict = {}
        for name in plc_tags.model_fields:
            tags = getattr(plc_tags, name)
            values = self._read(tags)
            data_dict[name] = values
        if "timestamp" not in data_dict:
            data_dict["timestamp"] = datetime.now().timestamp()
        return data_dict

    def read_input(self):
        """Read tags from PLC"""
        plc_tags = Tags().station
        data_dict = {}
        for name in plc_tags.model_fields:
            tags = getattr(plc_tags, name)
            values = self._read(tags)
            data_dict[name] = values
        if "timestamp" not in data_dict:
            data_dict["timestamp"] = datetime.now().timestamp()
        return data_dict

    def read_setting(self):
        plc_tags = Tags().setting
        data_dict = {}
        for name in plc_tags.model_fields:
            tags = getattr(plc_tags, name)
            values = self._read(tags)
            data_dict[name] = values
        return data_dict

    def update(self):
        """Wait some time"""
        time.sleep(self.sample_time)
