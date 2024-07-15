"""
This file contains the defination of tank model and pump station model.
"""

import logging

from .data import ControlData, StationBounds, StationData

from collections import deque
from typing import Deque

import numpy as np


class Tank:
    """Real Reservoir for simulation.
    area: the area of the pipe network and the reservoir
    height: the initial height of the water in the reservoir
    timestamp: the initial time (in seconds)
    inflow: the inflow rate (in m3/h)
    """

    def __init__(
        self,
        area: float,
        water_level: float,
        timestamp: float,
    ):
        self._timestamp = timestamp
        self._area = area
        self._water_level = water_level
        self._inflow_deque: Deque[float] = deque([0.0], maxlen=100)

    def get_inflow(self):
        """Compute inflow rate"""
        return np.mean(self._inflow_deque)

    def get_water_level(self):
        """Get water level"""
        return self._water_level

    def update(self, timestamp: float, water_level: float, outflow: float):
        """Update tank status
        outflow: total outflow rate in m3/h
        """
        dt = timestamp - self._timestamp
        if np.isclose(dt, 0):
            return self
        dh = water_level - self._water_level
        inflow = dh * self._area / dt * 3600 + outflow
        self._inflow_deque.append(inflow)
        self._timestamp = timestamp
        self._water_level = water_level
        return self


class PumpingStation:
    """Dataclass to store the models in a pumping station.
    tank_area: the area of the pipe network and the reservoir
    water_level: the initial height of the water in the reservoir
    """

    def __init__(
        self,
        sec_models: list,
        flow_models: list,
        variable_speed: list,
        tank_area: float,
        station_data: StationData,
        station_bounds: StationBounds,
    ):
        self.sec_models = sec_models
        self.flow_models = flow_models
        self.variable_speed = variable_speed
        self.tank_area = tank_area
        self.station_data = station_data
        self.station_bounds = station_bounds

    def update(
        self,
        timestamp: float,
        inflow: float,
        control_data: ControlData,
    ):
        """Compute the change path of sec, outflow, and water level.

        Parameters
        ----------
        inflow : float
            Current inflow rate (in m^3/h).


        Returns
        -------
        sec_pred : array-like of shape (n_pumps,)
            The prediction of SEC of each pump.

        outflow_pred : array-like of shape (n_pumps,)
            The prediction of outflow rate of each pump.

        """
        # Add input check
        sec_pred = []
        outflow_pred = []

        for i, switch_temp in enumerate(control_data.switch):
            if i in self.variable_speed:
                X_temp = [[self.station_data.water_level, control_data.speed[i]]]
            else:
                X_temp = [[self.station_data.water_level]]
            if switch_temp:
                sec_pred.append(self.sec_models[i].predict(X_temp).item())
                outflow_pred.append(self.flow_models[i].predict(X_temp).item())
            else:
                sec_pred.append(0)
                outflow_pred.append(0)

        netflow = inflow - sum(outflow_pred)
        delta_level = (
            netflow * (timestamp - self.station_data.timestamp) / 3600 / self.tank_area
        )
        water_level_temp = self.station_data.water_level + delta_level

        if water_level_temp < self.station_bounds.water_level[0]:
            logging.warning(
                "The tank is underflowing: water_level = %.2f.", water_level_temp
            )
            water_level_temp = self.station_bounds.water_level[0]
        elif water_level_temp > self.station_bounds.water_level[1]:
            logging.warning(
                "The tank is overflowing: water_level = %.2f.", water_level_temp
            )
            water_level_temp = self.station_bounds.water_level[1]

        self.station_data.timestamp = timestamp
        self.station_data.water_level = water_level_temp
        self.station_data.switch = control_data.switch
        self.station_data.speed = control_data.speed
        self.station_data.outflow = outflow_pred
        self.station_data.sec = sec_pred

        return self
