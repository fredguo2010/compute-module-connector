"""Read from / Write to API gateway, PLC, and Virtual pumping station."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import json

import joblib
import numpy as np

from ..base import BaseConnector
from ..data import ControlData, Setting, StationBounds, StationData
from ..model import PumpingStation

INIT_TIMESTAMP = datetime.strptime(
    "2024-01-01",
    "%Y-%m-%d",
).replace(tzinfo=timezone.utc).timestamp()

class VirtualConnector(BaseConnector):
    """Read from or write to a virtual station"""

    def __init__(self, sample_time: float | Literal["real_time"], **kwargs):
        super().__init__(sample_time=sample_time, **kwargs)

        # Init Config
        work_dir = Path.cwd()
        with open(work_dir / "src" / "config.json", "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        data_address = config_dict["DATA_ADDRESS"]
        models_address = config_dict["MODELS_ADDRESS"]
        n_pumps = config_dict["N_PUMPS"]

        init_station_data = StationData(
            water_level=4.6,
            switch=[0, 0, 0, 0, 1, 1, 1, 1],
            speed=[0, 0, 0, 0, 50, 50, 45, 45],
            outflow=[0, 0, 0, 0, 5000, 5000, 5000, 5000],
            sec=[0, 0, 0, 0, 0.05, 0.05, 0.04, 0.04],
        )

        init_control_data = ControlData(
            switch=[0, 0, 0, 0, 1, 1, 1, 1],
            speed=[0, 0, 0, 0, 50, 50, 45, 45],
            total_outflow_setpoint=0,
            outflow_setpoints=[0, 0, 0, 0, 0, 0, 0, 0],
        )

        init_setting_data = Setting(
            outflow_lower=6000,
            outflow_upper=20000,
            h_setpoint=[3],
            h_lower = 3,
            h_upper = 6.5,
            t_lower = [8.5],
            t_upper = [14],
            pid_kp=-1000,
            pid_ki=-5,
            pid_kb=1,
        )

        sec_models = []
        for idx in range(n_pumps):
            with open(
                work_dir / models_address / f"pump{idx+1}_sec.pkl",
                "rb",
            ) as file:
                sec_models += [joblib.load(file)]
        flow_models = []
        for idx in range(n_pumps):
            with open(
                work_dir / models_address / f"pump{idx+1}_flow.pkl",
                "rb",
            ) as file:
                flow_models += [joblib.load(file)]

        self.counter = 0
        self._update_timestamp()
        init_station_data.timestamp = self.timestamp
        init_control_data.timestamp = self.timestamp
        self.pump_station = PumpingStation(
            sec_models=sec_models,
            flow_models=flow_models,
            variable_speed=config_dict["VARIABLE_SPEED_PUMPS"],
            tank_area=config_dict["TANK_AREA"],
            station_data=init_station_data,
            station_bounds=StationBounds(),
        )
        self.control_data = init_control_data
        self.station_data = init_station_data
        self.setting_data = init_setting_data
        self._inflow_data = np.load(work_dir / data_address / "20240311.npy")
        self._inflow_sample_time = 20
        self._n_inflow = len(self._inflow_data)

    def write_output(self, data: ControlData):
        """Write data to PLC"""
        if not isinstance(data, ControlData):
            msg = "API Connector can only write ControlData."
            logging.error(msg)
            raise TypeError(msg)
        self.control_data = data

    def _update_timestamp(self):
        if self.sample_time == "real_time":
            self.timestamp = datetime.now(tz=timezone.utc).timestamp()
        else:
            self.timestamp = self.counter * self.sample_time + INIT_TIMESTAMP

    def read_input(self):
        """Read tags from PLC"""
        return self.station_data.model_dump()

    def read_setting(self):
        """Read setting from PLC"""
        return self.setting_data.model_dump()

    def update(self):
        """Update station data"""
        self.counter += 1
        self._update_timestamp()
        inflow = self._inflow_data[
            self.counter % self._n_inflow
        ]

        # Total outflow setpoint to pump speed
        switch_off_mask = np.logical_not(list(map(bool, self.control_data.switch)))
        speed_temp = np.full_like(
            self.control_data.speed,
            self.pump_station.station_bounds.speed[1],
            dtype=float,
        )
        speed_temp[self.pump_station.variable_speed] = np.array(
            self.control_data.speed
        )[self.pump_station.variable_speed]
        speed_temp[switch_off_mask] = 0

        self.control_data.speed = speed_temp.tolist()

        station_data = self.pump_station.update(
            timestamp=self.timestamp,
            inflow=inflow,
            control_data=self.control_data,
        ).station_data

        self.station_data = station_data
