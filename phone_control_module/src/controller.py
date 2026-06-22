"""
Phone Controller - Main interface for phone control.

Integrates all services and provides a unified API for Hermes Agent tools.
"""

import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import base64
import io

from .backend import ADBBackend
from .services import ScreenService, InputService, AppService

logger = logging.getLogger(__name__)


class PhoneController:
    """
    Main controller for Android phone operations.
    
    Provides high-level methods for screen control, input, and app management.
    Designed for integration with Hermes Agent tool system.
    """
    
    def __init__(self, device_ip: Optional[str] = None, auto_connect: bool = True):
        """
        Initialize phone controller.
        
        Args:
            device_ip: IP address for WiFi ADB (None for USB)
            auto_connect: Automatically connect on initialization
        """
        self.device_ip = device_ip
        self.adb = ADBBackend(device_ip=device_ip)
        self.screen = ScreenService(self.adb)
        self.input = InputService(self.adb)
        self.apps = AppService(self.adb)
        
        if auto_connect:
            self.connect()
    
    def connect(self) -> bool:
        """
        Connect to phone.
        
        Returns:
            True if connection successful
        """
        if self.device_ip:
            return self.adb.connect_wifi()
        else:
            return self.adb.connect_usb()
    
    def disconnect(self):
        """Disconnect from phone."""
        self.adb.disconnect()
    
    def is_connected(self) -> bool:
        """Check if connected to phone."""
        return self.adb.is_connected()
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self.adb.get_device_info()
    
    # Screen Operations
    
    def screenshot(self, save_path: Optional[str] = None) -> Image.Image:
        """
        Take a screenshot.
        
        Args:
            save_path: Optional path to save image
            
        Returns:
            PIL Image object
        """
        img = self.screen.screenshot()
        if save_path:
            img.save(save_path)
            logger.info(f"Screenshot saved to {save_path}")
        return img
    
    def screenshot_base64(self) -> str:
        """
        Take screenshot and return as base64 string.
        
        Returns:
            Base64 encoded PNG string
        """
        img = self.screen.screenshot()
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def get_screen_elements(self) -> List[Dict[str, Any]]:
        """
        Get all visible UI elements.
        
        Returns:
            List of element dictionaries
        """
        return self.screen.get_ui_elements()
    
    def find_element(self, text_contains: Optional[str] = None,
                     class_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find UI element by criteria.
        
        Args:
            text_contains: Text substring to match
            class_name: Class name to match
            
        Returns:
            Element dictionary or None
        """
        return self.screen.find_element(text_contains, class_name)
    
    # Input Operations
    
    def tap(self, x: int, y: int):
        """Tap at coordinates."""
        self.input.tap(x, y)
    
    def tap_on(self, text_contains: str) -> bool:
        """
        Tap on element containing text.
        
        Args:
            text_contains: Text to search for
            
        Returns:
            True if element found and tapped
        """
        elem = self.screen.find_element(text_contains=text_contains)
        if elem:
            self.input.tap_element(elem)
            return True
        return False
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, 
              duration_ms: int = 300):
        """Perform swipe gesture."""
        self.input.swipe(start_x, start_y, end_x, end_y, duration_ms)
    
    def scroll(self, direction: str = "down"):
        """Scroll screen."""
        self.input.scroll(direction)
    
    def type_text(self, text: str):
        """Type text."""
        self.input.type_text(text)
    
    def press_key(self, key_code: int):
        """Press hardware key."""
        self.input.press_key(key_code)
    
    def press_home(self):
        """Press home button."""
        self.input.press_key(3)
    
    def press_back(self):
        """Press back button."""
        self.input.press_key(4)
    
    def press_recent(self):
        """Press recent apps button."""
        self.input.press_key(187)
    
    # App Operations
    
    def launch_app(self, package_name: str):
        """Launch an app."""
        self.apps.launch_app(package_name)
    
    def get_current_app(self) -> Optional[str]:
        """Get current app package name."""
        return self.apps.get_current_app()
    
    def list_apps(self) -> List[str]:
        """List installed apps."""
        return self.apps.list_installed_apps()
    
    # Tool definitions for Hermes Agent integration
    
    @staticmethod
    def get_hermes_tools() -> List[Dict[str, Any]]:
        """
        Return tool definitions for Hermes Agent registration.
        
        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "name": "phone_screenshot",
                "description": "Take a screenshot of the phone screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "save_path": {"type": "string", "description": "Optional path to save"}
                    }
                }
            },
            {
                "name": "phone_tap",
                "description": "Tap at specified coordinates or on UI element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate"},
                        "y": {"type": "integer", "description": "Y coordinate"},
                        "text": {"type": "string", "description": "Or tap on element with this text"}
                    }
                }
            },
            {
                "name": "phone_swipe",
                "description": "Perform swipe gesture",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer"},
                        "start_y": {"type": "integer"},
                        "end_x": {"type": "integer"},
                        "end_y": {"type": "integer"},
                        "duration_ms": {"type": "integer", "default": 300}
                    }
                }
            },
            {
                "name": "phone_type",
                "description": "Type text into focused input field",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to type"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "phone_launch_app",
                "description": "Launch an app by package name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "package": {"type": "string", "description": "App package name"}
                    },
                    "required": ["package"]
                }
            },
            {
                "name": "phone_get_elements",
                "description": "Get all visible UI elements on screen",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "phone_press_key",
                "description": "Press hardware key (Home, Back, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "enum": ["home", "back", "recent", "power"]}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "phone_scroll",
                "description": "Scroll screen in specified direction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["up", "down", "left", "right"]}
                    },
                    "required": ["direction"]
                }
            }
        ]
