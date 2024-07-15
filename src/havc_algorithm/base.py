"""Base classes."""

from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """Base class for Connector."""

    def __init__(
        self,
        sample_time,
        **kwargs,
    ):
        self.sample_time = sample_time
        self.__dict__.update(kwargs)

    @abstractmethod
    def write_output(self, data) -> None:
        """Abstract method for writing output"""

    @abstractmethod
    def read_input(self) -> dict:
        """Abstract method for reading input"""
        return {"timestamp": 0}

    @abstractmethod
    def update(self) -> None:
        """Abstract method for updating/waiting"""

    def read_setting(self) -> dict:
        """Read settings for AutoFlow"""
        return {"timestamp": 0}
