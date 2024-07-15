"""Read from / Write to API gateway."""

import ast
import logging
import time
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..base import BaseConnector
from ..data import ControlData, StationData


class APIConnector(BaseConnector):
    """Read from or write to API."""

    def __init__(self, sample_time: float, path: str, **kwargs):
        super().__init__(sample_time=sample_time, path=path, **kwargs)
        # Increase the times of retries
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def write_output(self, data: ControlData):
        """Write data to API"""
        if not isinstance(data, ControlData):
            msg = "API Connector can only write ControlData."
            logging.error(msg)
            raise TypeError(msg)

        output_data = {
            "output.outflow_setpoint": data.outflow_setpoints,
            "output.speed": data.speed,
            "output.switch": data.switch,
            "output.total_outflow_setpoint": data.total_outflow_setpoint,
        }

        self.session.post(
            url=getattr(self, "path") + "output",
            json=output_data,
            timeout=5,
        )

    def read_input(self):
        """Read data from API"""
        response = self.session.get(
            url=getattr(self, "path") + "input",
            timeout=5,
        )
        input_data = ast.literal_eval(response.text)
        input_data["timestamp"] = time.mktime(
            datetime.strptime(
                input_data["timestamp"],
                "%Y-%m-%d %H:%M:%S",
            ).timetuple()
        )
        station_data = StationData(
            timestamp=input_data["timestamp"],
            water_level=input_data["input.water_level"],
            switch=input_data["input.switch"],
            speed=input_data["input.speed"],
            outflow=input_data["input.outflow"],
            sec=input_data["input.sec"],
        )
        return station_data

    def read_setting(self):
        """TEMP: to be read from database."""
        return {
            "outflow_lower": 10000,
            "outflow_upper": 30000,
            "h_setpoint": 3.8,
            "pid_kp": -1000,
            "pid_ki": -1,
            "pid_kb": 1,
        }

    def update(self):
        """Wait some time"""
        time.sleep(self.sample_time)
