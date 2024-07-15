"""Utils for common purposes"""

import numpy as np

from .data import PIDSetting


class StopwatchGroup:
    """A group of stopwatches to calcuate cumulative times"""

    def __init__(self, n_watches: int, timestamp: float):
        self.cum_time = np.zeros(n_watches, dtype=float)
        self.timestamp = timestamp

    def update(self, timestamp: float, switch_mask: list[bool]):
        """Update the cumulative run times"""
        self.cum_time[switch_mask] += timestamp - self.timestamp
        self.timestamp = timestamp
        return self

    def get_cum_time(self):
        """Get cumulative times"""
        return self.cum_time.tolist()


class PID:
    """Simple PID"""

    def __init__(self, setting: PIDSetting, t_init: float = 0):
        self.update_setting(setting)

        # initialize stored data
        self._e_last = 0
        self._t_last = t_init
        self._ei = 0
        self._back_calc = 0
        self._cv_last = setting.cv_bar

    def update_setting(self, setting: PIDSetting):
        """Update pid setting without re-initialize"""
        self.setting = setting

    def update(self, t: float, pv: float, sp: float):
        """PID calculations"""
        if np.isclose(t, self._t_last, rtol=0):
            return self._cv_last
        e = sp - pv
        ep = self.setting.kp * e

        self._ei = self._ei + self.setting.ki * e * (t - self._t_last) + self._back_calc
        self._ei = (
            self.setting.ei_min
            if self._ei < self.setting.ei_min
            else (self.setting.ei_max if self._ei > self.setting.ei_max else self._ei)
        )

        ed = self.setting.kd * (e - self._e_last) / (t - self._t_last)

        cv_ubd = self.setting.cv_bar + ep + self._ei + ed
        cv = (
            self.setting.cv_min
            if cv_ubd < self.setting.cv_min
            else self.setting.cv_max
            if cv_ubd > self.setting.cv_max
            else cv_ubd
        )
        self._back_calc = self.setting.kb * (cv - cv_ubd)

        # update stored data for next iteration
        self._e_last = e
        self._t_last = t
        self._cv_last = cv
        return cv
