"""
PROJECT NEXUS: Mobile Node Agent (Pixel 7a)
Specialized agent for Android devices with sensor fusion, ADB control,
and lightweight on-device inference capabilities.
"""

import asyncio
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import logging

# ADB and device imports (would be installed in production)
try:
    import adb_shell
    from adb_shell.adb_device import AdbDeviceUsb, AdbDeviceTcp
    ADB_AVAILABLE = True
except ImportError:
    ADB_AVAILABLE = False
    logger = logging.getLogger("nexus.mobile")
    logger.warning("adb-shell not installed, running in simulation mode")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.mobile")

@dataclass
class SensorData:
    timestamp: float
    battery_level: float = 0.0
    battery_status: str = "unknown"  # charging, discharging, full
    signal_strength: float = 0.0
    wifi_connected: bool = False
    gps_location: Optional[Dict[str, float]] = None
    accelerometer: Optional[Dict[str, float]] = None
    screen_on: bool = False
    foreground_app: Optional[str] = None

@dataclass
class MobileTask:
    id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timeout: float = 30.0

class MobileNodeAgent:
    """
    Specialized agent for Pixel 7a (Android 16) that:
    - Manages ADB connections (USB/WiFi)
    - Collects sensor data
    - Executes mobile-specific actions
    - Runs lightweight on-device ML models
    """
    
    def __init__(self, device_id: str = "pixel7a", connection_type: str = "wifi"):
        self.device_id = device_id
        self.connection_type = connection_type
        self.device: Optional[Any] = None
        self.connected = False
        
        self.sensor_data = SensorData(timestamp=time.time())
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.capabilities = [
            "gps", "camera", "cellular", "nfc", 
            "sensor_fusion", "touch_input", "voice_input"
        ]
        
        self._running = False
        self._device_ip: Optional[str] = None
    
    async def connect(self, device_ip: str = None) -> bool:
        """Connect to the Android device via ADB"""
        if not ADB_AVAILABLE:
            logger.info(f"[SIMULATION] Connecting to {self.device_id} at {device_ip or 'USB'}")
            self.connected = True
            self._device_ip = device_ip or "usb"
            return True
        
        try:
            if self.connection_type == "wifi" and device_ip:
                self.device = AdbDeviceTcp(device_ip, 5555)
                self.device.connect(rsa_key_path=None)
            else:
                self.device = AdbDeviceUsb()
                self.device.connect(rsa_key_path=None)
            
            self.connected = True
            self._device_ip = device_ip or "usb"
            logger.info(f"Connected to {self.device_id} via {self.connection_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the device"""
        if self.device and hasattr(self.device, 'close'):
            self.device.close()
        self.connected = False
        logger.info(f"Disconnected from {self.device_id}")
    
    async def get_sensor_data(self) -> SensorData:
        """Fetch current sensor data from the device"""
        if not self.connected:
            # Return simulated data
            return self._simulate_sensor_data()
        
        try:
            # In production, these would be real ADB commands
            # battery = await self._adb_shell("dumpsys battery")
            # location = await self._adb_shell("pm location last")
            # For now, simulate
            return self._simulate_sensor_data()
            
        except Exception as e:
            logger.error(f"Error fetching sensor data: {e}")
            return self.sensor_data
    
    def _simulate_sensor_data(self) -> SensorData:
        """Simulate sensor data for demo/testing"""
        self.sensor_data = SensorData(
            timestamp=time.time(),
            battery_level=78.5,
            battery_status="discharging",
            signal_strength=-85,
            wifi_connected=True,
            gps_location={"lat": 40.7128, "lon": -74.0060},
            accelerometer={"x": 0.1, "y": 9.8, "z": 0.2},
            screen_on=True,
            foreground_app="com.android.chrome"
        )
        return self.sensor_data
    
    async def execute_action(self, action: str, params: Dict = None) -> Dict:
        """Execute a mobile-specific action"""
        params = params or {}
        
        action_handlers = {
            "tap": self._tap,
            "swipe": self._swipe,
            "type": self._type_text,
            "launch_app": self._launch_app,
            "get_screenshot": self._get_screenshot,
            "get_notifications": self._get_notifications,
            "send_sms": self._send_sms,
            "make_call": self._make_call,
            "get_location": self._get_location,
            "set_wifi": self._set_wifi,
            "get_battery": self._get_battery,
            "read_nfc": self._read_nfc
        }
        
        handler = action_handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        try:
            result = await handler(**params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _tap(self, x: int, y: int):
        """Tap at coordinates"""
        if self.connected and self.device:
            # Real: self.device.shell(f"input tap {x} {y}")
            pass
        logger.info(f"[MOBILE] Tap at ({x}, {y})")
        return {"tapped": [x, y]}
    
    async def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe from one point to another"""
        if self.connected and self.device:
            # Real: self.device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            pass
        logger.info(f"[MOBILE] Swipe ({x1},{y1}) -> ({x2},{y2})")
        return {"swiped": [[x1, y1], [x2, y2]]}
    
    async def _type_text(self, text: str):
        """Type text using input method"""
        if self.connected and self.device:
            # Real: self.device.shell(f"input text '{text.replace(' ', '%s')}'")
            pass
        logger.info(f"[MOBILE] Type: {text[:50]}...")
        return {"typed": text}
    
    async def _launch_app(self, package: str):
        """Launch an app by package name"""
        if self.connected and self.device:
            # Real: self.device.shell(f"monkey -p {package} 1")
            pass
        logger.info(f"[MOBILE] Launch app: {package}")
        return {"launched": package}
    
    async def _get_screenshot(self) -> str:
        """Capture screenshot"""
        logger.info("[MOBILE] Capturing screenshot")
        return "base64_encoded_image_data_placeholder"
    
    async def _get_notifications(self) -> List[Dict]:
        """Get current notifications"""
        logger.info("[MOBILE] Fetching notifications")
        return [
            {"app": "com.whatsapp", "title": "John", "text": "Hey, running late"},
            {"app": "com.gmail", "title": "Flight Update", "text": "Gate changed to B12"}
        ]
    
    async def _send_sms(self, phone: str, message: str):
        """Send SMS message"""
        logger.info(f"[MOBILE] Send SMS to {phone}: {message[:30]}...")
        return {"sent": True, "to": phone}
    
    async def _make_call(self, phone: str):
        """Initiate phone call"""
        logger.info(f"[MOBILE] Calling {phone}")
        return {"calling": phone}
    
    async def _get_location(self) -> Dict:
        """Get current GPS location"""
        loc = self.sensor_data.gps_location or {"lat": 40.7128, "lon": -74.0060}
        return loc
    
    async def _set_wifi(self, enabled: bool):
        """Toggle WiFi"""
        logger.info(f"[MOBILE] WiFi {'enabled' if enabled else 'disabled'}")
        self.sensor_data.wifi_connected = enabled
        return {"wifi": enabled}
    
    async def _get_battery(self) -> Dict:
        """Get battery status"""
        return {
            "level": self.sensor_data.battery_level,
            "status": self.sensor_data.battery_status,
            "charging": self.sensor_data.battery_status == "charging"
        }
    
    async def _read_nfc(self) -> Optional[Dict]:
        """Read NFC tag (if present)"""
        logger.info("[MOBILE] Reading NFC...")
        # Would require actual NFC hardware access
        return None
    
    async def start_listening(self):
        """Start the mobile node task listener"""
        self._running = True
        asyncio.create_task(self._task_loop())
        asyncio.create_task(self._sensor_loop())
        logger.info(f"Mobile node {self.device_id} started")
    
    def stop_listening(self):
        """Stop the mobile node"""
        self._running = False
        logger.info(f"Mobile node {self.device_id} stopped")
    
    async def _task_loop(self):
        """Process incoming tasks"""
        while self._running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                result = await self.execute_action(task.action, task.params)
                logger.debug(f"Task {task.id} completed: {result}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error: {e}")
    
    async def _sensor_loop(self):
        """Periodically update sensor data"""
        while self._running:
            await self.get_sensor_data()
            await asyncio.sleep(5)  # Update every 5 seconds
    
    def get_status(self) -> Dict:
        """Get current node status"""
        return {
            "device_id": self.device_id,
            "connected": self.connected,
            "connection_type": self._device_ip,
            "capabilities": self.capabilities,
            "sensor_data": {
                "battery": self.sensor_data.battery_level,
                "location": self.sensor_data.gps_location,
                "wifi": self.sensor_data.wifi_connected,
                "screen_on": self.sensor_data.screen_on
            },
            "queue_size": self.task_queue.qsize()
        }

# Singleton instance
mobile_node = MobileNodeAgent()

if __name__ == "__main__":
    async def demo():
        # Connect to device
        await mobile_node.connect("192.168.1.100")
        await mobile_node.start_listening()
        
        # Queue some tasks
        await mobile_node.task_queue.put(MobileTask(
            id="1", action="launch_app", params={"package": "com.google.maps"}
        ))
        await mobile_node.task_queue.put(MobileTask(
            id="2", action="get_location"
        ))
        await mobile_node.task_queue.put(MobileTask(
            id="3", action="get_battery"
        ))
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Get status
        print("\nMobile Node Status:")
        status = mobile_node.get_status()
        print(json.dumps(status, indent=2))
        
        await mobile_node.disconnect()
        mobile_node.stop_listening()
    
    asyncio.run(demo())
