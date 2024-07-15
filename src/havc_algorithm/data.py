"""
This file contains schema definitions.
"""

from typing import Annotated

from pydantic import BaseModel, Field, conlist, model_validator


class PIDSetting(BaseModel):
    """Configurations of PID controllers"""

    kp: float
    ki: float
    kd: float = 0
    cv_min: float
    cv_max: float
    cv_bar: float
    kb: float = 0
    ei_min: float
    ei_max: float

    @model_validator(mode="after")
    def check_min_max(self) -> "PIDSetting":
        """Check if min <= max"""
        if self.cv_min > self.cv_max:
            raise ValueError(
                "cv_min should less or equal than cv_max but got "
                f"cv_min: {self.cv_min} and cv_max: {self.cv_max}."
            )
        if self.ei_min > self.ei_max:
            raise ValueError(
                "ei_min should less or equal than ei_max but got "
                f"ei_min: {self.ei_min} and cv_max: {self.ei_max}."
            )
        return self


class Config(BaseModel):
    """Global configuartions for AutoFlow"""

    n_pumps: int = Field(gt=0)
    opt_flow: Annotated[list, conlist(Annotated[float, Field(gt=0)], min_length=1)]
    min_flow: Annotated[list, conlist(Annotated[float, Field(gt=0)], min_length=1)]
    max_flow: Annotated[list, conlist(Annotated[float, Field(gt=0)], min_length=1)]
    vsp_index: list
    area: float
    water_level_limits: list[float] = [0, 10]
    speed_limits: list[float] = [40, 50]
    max_saturation_time: float = 300
    max_cum_time_diff: float = 86400
    min_switch_time_interval: float = 3600


class Setting(BaseModel):
    """Local configuartions for AutoFlow"""

    outflow_lower: float
    outflow_upper: float
    # water level setpoint during t_lower and t_upper
    h_setpoint: Annotated[list, conlist(Annotated[float, Field(gt=0)], min_length=1)]
    h_lower: float
    h_upper: float
    # hour, i.e. 15.5 means 3:30 pm
    t_lower: Annotated[list, conlist(Annotated[float, Field(ge=0, lt=24)], min_length=1)]
    t_upper: Annotated[list, conlist(Annotated[float, Field(gt=0, lt=24)], min_length=1)] # hour
    pid_kp: float
    pid_ki: float
    pid_kb: float


class ControlData(BaseModel):
    """Status of AI recommendation.
    speed : array-like of shape (n_pumps,)
            The speed of each pump.

    swtich : array-like of shape (n_pumps,)
        The swtich on(1)/off(0) of each pump.

    """

    timestamp: float = 0
    switch: list[int] = [0]
    speed: list[float] = [0]
    total_outflow_setpoint: float = 0
    outflow_setpoints: list[float] = [0]
    h_setpoint: float = 0
    inflow: float = 0


class StationData(BaseModel):
    """Request message body."""

    timestamp: float = 0
    # water_level: float = 0
    # switch: list[int] = [0]
    # speed: list[float] = [0]
    # outflow: list[float] = [0]
    # sec: list[float] = [0]
    # tag_return_temperatue: float = 0
    Tag_INT: int = 0
    Tag_TW: float = 0.0
    Tag_CTW_SP: float = 0.0

class CoolingTemp(BaseModel):
    return_temperature: float = 0

class StationBounds(BaseModel):
    """Upper and lower bounds for the StationData."""

    water_level: list[float] = [0, 10]
    speed: list[float] = [40, 50]
