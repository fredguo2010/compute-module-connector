"""Read from / Write to PLC."""

import logging
import time
from datetime import datetime

from pydantic import BaseModel

from ..base import BaseConnector
from ..data import ControlData, Setting, StationData
from ._compute import Compute
from ._ethernet import Tags

TAG_TYPES = {
    "Tag_INT": "int",
    "Tag_TW": "real", # 湿球温度点位
    "Tag_CTW_SP": 'real' # 冷却水回水温度
}

for i in range(50):
    TAG_TYPES[f"Tag_DINT[{i}]"] = "dint"

class BackplaneConnector(BaseConnector):
    """Read from or write to PLC tags."""

    def __init__(self, sample_time: float, path: str, **kwargs):
        super().__init__(sample_time=sample_time, path=path, **kwargs)
        self._plc = Compute()

    def _read(self, tags: str | list[str]):
        if isinstance(tags, str):
            return self._plc.read_tag(
                tags, cip_dtype=TAG_TYPES[tags], length=1, slot=getattr(self, "path")
            )
        return [
            self._plc.read_tag(
                tag, cip_dtype=TAG_TYPES[tag], length=1, slot=getattr(self, "path")
            )
            for tag in tags
        ]

    def _write(self, tags: str | list[str], values):
        if isinstance(tags, str):
            self._plc.write_tag(
                tags, cip_dtype=TAG_TYPES[tags], data=values, slot=getattr(self, "path")
            )
        else:
            for n, tag in enumerate(tags):
                self._plc.write_tag(
                    tag,
                    cip_dtype=TAG_TYPES[tag],
                    data=values[n],
                    slot=getattr(self, "path"),
                )

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
