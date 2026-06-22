"""
ADB Backend - Handles Android Debug Bridge connections and commands.

Supports both USB and WiFi ADB connections with auto-reconnect capabilities.
Optimized for Android 16 (Pixel 7a) security model.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from adb_shell.adb_device import AdbDeviceUsb, AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
import os
import time

logger = logging.getLogger(__name__)


class ADBBackend:
    """
    Low-level ADB connection manager.
    
    Handles device discovery, connection, authentication, and command execution.
    """
    
    def __init__(self, device_ip: Optional[str] = None, port: int = 5555):
        """
        Initialize ADB backend.
        
        Args:
            device_ip: IP address for WiFi ADB (None for USB)
            port: ADB port (default 5555 for WiFi)
        """
        self.device_ip = device_ip
        self.port = port
        self.device: Optional[AdbDeviceTcp | AdbDeviceUsb] = None
        self.connected = False
        self._auth_keys = self._load_or_generate_keys()
    
    def _load_or_generate_keys(self) -> Tuple[PythonRSASigner, PythonRSASigner]:
        """Load existing RSA keys or generate new ones for ADB authentication."""
        key_path = os.path.expanduser("~/.android/adbkey")
        pub_key_path = f"{key_path}.pub"
        
        if not os.path.exists(key_path):
            logger.info("Generating new ADB RSA keys...")
            keygen(key_path)
        
        with open(key_path, "rb") as f:
            priv_key = f.read()
        with open(pub_key_path, "rb") as f:
            pub_key = f.read()
        
        signer = PythonRSASigner(pub_key, priv_key)
        return signer, signer
    
    def connect_usb(self) -> bool:
        """
        Connect to device via USB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.device = AdbDeviceUsb()
            self.device.connect(rsa_keys=[self._auth_keys[0]], auth_timeout_s=5.0)
            self.connected = True
            logger.info("Connected to device via USB")
            return True
        except Exception as e:
            logger.error(f"USB connection failed: {e}")
            self.connected = False
            return False
    
    def connect_wifi(self, ip: Optional[str] = None) -> bool:
        """
        Connect to device via WiFi ADB.
        
        Args:
            ip: Device IP address (uses stored IP if None)
            
        Returns:
            True if connection successful, False otherwise
        """
        device_ip = ip or self.device_ip
        if not device_ip:
            logger.error("No device IP specified")
            return False
        
        try:
            self.device = AdbDeviceTcp(device_ip, self.port)
            self.device.connect(rsa_keys=[self._auth_keys[0]], auth_timeout_s=5.0)
            self.connected = True
            logger.info(f"Connected to {device_ip}:{self.port} via WiFi")
            return True
        except Exception as e:
            logger.error(f"WiFi connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from device."""
        if self.device:
            try:
                self.device.close()
            except:
                pass
        self.connected = False
        self.device = None
        logger.info("Disconnected from device")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to device.
        
        Returns:
            True if reconnection successful
        """
        self.disconnect()
        time.sleep(1)
        
        if self.device_ip:
            return self.connect_wifi()
        else:
            return self.connect_usb()
    
    def shell(self, command: str) -> str:
        """
        Execute shell command on device.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Command output as string
        """
        if not self.connected or not self.device:
            raise ConnectionError("Not connected to device")
        
        try:
            output = self.device.shell(command)
            return output.strip() if output else ""
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            # Attempt auto-reconnect
            if self.reconnect():
                output = self.device.shell(command)
                return output.strip() if output else ""
            raise
    
    def push(self, local_path: str, remote_path: str):
        """Push file to device."""
        if not self.connected or not self.device:
            raise ConnectionError("Not connected to device")
        
        with open(local_path, "rb") as f:
            self.device.push(f, remote_path)
        logger.debug(f"Pushed {local_path} to {remote_path}")
    
    def pull(self, remote_path: str, local_path: str):
        """Pull file from device."""
        if not self.connected or not self.device:
            raise ConnectionError("Not connected to device")
        
        with open(local_path, "wb") as f:
            self.device.pull(remote_path, f)
        logger.debug(f"Pulled {remote_path} to {local_path}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information.
        
        Returns:
            Dictionary with device properties
        """
        if not self.connected:
            return {}
        
        try:
            props = {
                "model": self.shell("getprop ro.product.model"),
                "manufacturer": self.shell("getprop ro.product.manufacturer"),
                "android_version": self.shell("getprop ro.build.version.release"),
                "sdk_version": self.shell("getprop ro.build.version.sdk"),
                "screen_size": self.shell("wm size"),
                "screen_density": self.shell("wm density"),
            }
            return props
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {}
    
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self.connected and self.device is not None
