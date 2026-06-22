"""Bluetooth LE controller for a remote-control T-rex toy."""
from . import protocol
from .client import Trex, TrexNotFound, find_device

__all__ = ["protocol", "Trex", "TrexNotFound", "find_device"]
__version__ = "0.2.0"
