"""Table for SQLite"""
from typing import Optional

from sqlmodel import Field, SQLModel

from .data import ControlData, StationData


class PumpTable(SQLModel, table=True):
    """Pump data model for SQL.

    Parameters
    ----------
    id : int, primary key
    timestamp : float
    pump_id : int
    control_switch : int
    control_speed : float
    outflow_setpoints : float
    switch : int
    speed : float
    outflow : float
    sec : float
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = 0
    pump_id: int = 0
    control_switch: int = 0
    control_speed: float = 0
    outflow_setpoint: float = 0
    switch: int = 0
    speed: float = 0
    outflow: float = 0
    sec: float = 0


class StationTable(SQLModel, table=True):
    """Station data model for SQL

    Parameters
    ----------
    id : int, primary key
    timestamp : float
    water_level : float
    total_outflow_setpoint : float
    total_outflow : float
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = 0
    water_level: float = 0
    total_outflow_setpoint: float = 0
    total_outflow: float = 0
    h_setpoint: float = 0
    inflow: float = 0
    sec: float = 0


def data2table(station_data: StationData, control_data: ControlData, n_pumps: int):
    """Save data to SQL.

    Parameters
    ----------
    station_data : StationData
        Data of pump station measurements.
    control_data : ControlData
        Data of control signals.
    """
    total_outflow = sum(station_data.outflow)
    if total_outflow == 0:
        total_sec = 0
    else:
        total_sec = sum(
            station_data.sec[i]*station_data.outflow[i] for i in range(n_pumps)
        )/total_outflow
    station_table = StationTable(
        timestamp=station_data.timestamp,
        water_level=station_data.water_level,
        total_outflow_setpoint=control_data.total_outflow_setpoint,
        total_outflow=total_outflow,
        h_setpoint=control_data.h_setpoint,
        inflow=control_data.inflow,
        sec=total_sec,
    )
    pump_table_list = []
    for i in range(n_pumps):
        pump_table_list += [
            PumpTable(
                timestamp=control_data.timestamp,
                pump_id=i,
                control_switch=control_data.switch[i],
                control_speed=control_data.speed[i],
                outflow_setpoint=control_data.outflow_setpoints[i],
                switch=station_data.switch[i],
                speed=station_data.speed[i],
                outflow=station_data.outflow[i],
                sec=station_data.sec[i],
            )
        ]
    return station_table, pump_table_list
