"""
Android Phone Control Module for Hermes Agent

Provides ADB-based control of Android devices, optimized for Pixel 7a (Android 16).
Supports both USB and WiFi ADB connections.
"""

from .controller import PhoneController
from .backend import ADBBackend
from .services import ScreenService, InputService, AppService

__version__ = "0.1.0"
__all__ = [
    "PhoneController",
    "ADBBackend",
    "ScreenService",
    "InputService",
    "AppService",
]
