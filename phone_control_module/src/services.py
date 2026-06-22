"""
Services for phone control - Screen, Input, and App management.

Provides high-level abstractions for common phone operations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io
import base64
import time

logger = logging.getLogger(__name__)


class ScreenService:
    """Handles screen capture and UI element analysis."""
    
    def __init__(self, adb_backend):
        self.adb = adb_backend
    
    def screenshot(self) -> Image.Image:
        """
        Capture current screen.
        
        Returns:
            PIL Image object
        """
        # Use screencap command (built-in Android)
        output = self.adb.shell("screencap -p")
        
        # Handle binary data from screencap
        if isinstance(output, bytes):
            # Remove any trailing nulls and handle line endings
            clean_data = output.replace(b'\r\n', b'\n')
            img = Image.open(io.BytesIO(clean_data))
        else:
            # Fallback: save to file and pull
            remote_path = "/data/local/tmp/screenshot.png"
            local_path = "/tmp/screenshot.png"
            self.adb.shell(f"screencap -p {remote_path}")
            self.adb.pull(remote_path, local_path)
            img = Image.open(local_path)
        
        return img.convert("RGB")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Returns:
            (width, height) tuple
        """
        size_output = self.adb.shell("wm size")
        # Parse "Physical size: 1080x2400"
        if "Physical size:" in size_output:
            dims = size_output.split(":")[1].strip()
            width, height = map(int, dims.split("x"))
            return (width, height)
        return (1080, 2400)  # Default Pixel 7a resolution
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """
        Get all visible UI elements using uiautomator dump.
        
        Returns:
            List of element dictionaries with text, bounds, class, etc.
        """
        # Dump UI hierarchy to XML
        self.adb.shell("uiautomator dump /data/local/tmp/ui.xml")
        
        # Pull the XML file
        import subprocess
        try:
            # Try to pull and parse XML
            local_xml = "/tmp/ui_dump.xml"
            self.adb.pull("/data/local/tmp/ui.xml", local_xml)
            
            # Parse XML (simplified - full implementation would use xml.etree)
            elements = []
            with open(local_xml, 'r', encoding='utf-8') as f:
                content = f.read()
                # Basic parsing - extract nodes with bounds
                import re
                pattern = r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="([^"]*)"[^>]*class="([^"]*)"'
                matches = re.findall(pattern, content)
                
                for match in matches:
                    x1, y1, x2, y2, text, cls = match
                    elements.append({
                        "bounds": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                        "text": text,
                        "class": cls.split(".")[-1],  # Get simple class name
                        "center_x": (int(x1) + int(x2)) // 2,
                        "center_y": (int(y1) + int(y2)) // 2,
                    })
            
            return elements
        except Exception as e:
            logger.error(f"Failed to parse UI elements: {e}")
            return []
    
    def find_element(self, text_contains: Optional[str] = None, 
                     class_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find a UI element by criteria.
        
        Args:
            text_contains: Text substring to match
            class_name: Class name to match
            
        Returns:
            Element dictionary or None
        """
        elements = self.get_ui_elements()
        
        for elem in elements:
            match = True
            if text_contains and text_contains.lower() not in elem["text"].lower():
                match = False
            if class_name and class_name.lower() not in elem["class"].lower():
                match = False
            
            if match:
                return elem
        
        return None


class InputService:
    """Handles touch input, gestures, and text input."""
    
    def __init__(self, adb_backend):
        self.adb = adb_backend
        self.screen = ScreenService(adb_backend)
    
    def tap(self, x: int, y: int):
        """
        Tap at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.adb.shell(f"input tap {x} {y}")
        logger.debug(f"Tapped at ({x}, {y})")
    
    def tap_element(self, element: Dict[str, Any]):
        """
        Tap on a UI element.
        
        Args:
            element: Element dictionary from get_ui_elements()
        """
        center_x = element.get("center_x")
        center_y = element.get("center_y")
        
        if center_x and center_y:
            self.tap(center_x, center_y)
        else:
            bounds = element.get("bounds", {})
            x1, x2 = bounds.get("x1", 0), bounds.get("x2", 0)
            y1, y2 = bounds.get("y1", 0), bounds.get("y2", 0)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            self.tap(center_x, center_y)
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, 
              duration_ms: int = 300):
        """
        Perform swipe gesture.
        
        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate
            duration_ms: Swipe duration in milliseconds
        """
        self.adb.shell(f"input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}")
        logger.debug(f"Swiped from ({start_x},{start_y}) to ({end_x},{end_y})")
    
    def scroll(self, direction: str = "down"):
        """
        Scroll screen in specified direction.
        
        Args:
            direction: "up", "down", "left", or "right"
        """
        width, height = self.screen.get_screen_size()
        center_x = width // 2
        center_y = height // 2
        
        if direction == "down":
            self.swipe(center_x, center_y * 1.5, center_x, center_y * 0.5)
        elif direction == "up":
            self.swipe(center_x, center_y * 0.5, center_x, center_y * 1.5)
        elif direction == "left":
            self.swipe(center_x * 1.5, center_y, center_x * 0.5, center_y)
        elif direction == "right":
            self.swipe(center_x * 0.5, center_y, center_x * 1.5, center_y)
    
    def type_text(self, text: str):
        """
        Type text using input method.
        
        Args:
            text: Text to type
        """
        # Escape special characters
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        self.adb.shell(f"input text '{escaped}'")
        logger.debug(f"Typed: {text[:50]}...")
    
    def long_press(self, x: int, y: int, duration_ms: int = 1000):
        """
        Long press at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration_ms: Press duration
        """
        self.adb.shell(f"input swipe {x} {y} {x} {y} {duration_ms}")
        logger.debug(f"Long pressed at ({x}, {y}) for {duration_ms}ms")
    
    def press_key(self, key_code: int):
        """
        Press hardware key.
        
        Common key codes:
        - 3: HOME
        - 4: BACK
        - 187: APP_SWITCH (Recent apps)
        - 26: POWER
        - 24: VOLUME_UP
        - 25: VOLUME_DOWN
        
        Args:
            key_code: Android key code
        """
        self.adb.shell(f"input keyevent {key_code}")
        logger.debug(f"Pressed key {key_code}")


class AppService:
    """Handles app management operations."""
    
    def __init__(self, adb_backend):
        self.adb = adb_backend
    
    def launch_app(self, package_name: str):
        """
        Launch an app by package name.
        
        Args:
            package_name: App package name (e.g., "com.whatsapp")
        """
        # Get launch activity using cmd package
        try:
            output = self.adb.shell(f"cmd package resolve-activity --components {package_name}")
            # Parse activity from output
            for line in output.split("\n"):
                if "Activities:" in line or "component=" in line.lower():
                    activity = line.strip().split("/")[-1]
                    self.adb.shell(f"am start -n {package_name}/{activity}")
                    logger.info(f"Launched {package_name}")
                    return
        except:
            pass
        
        # Fallback: use monkey command
        self.adb.shell(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
        logger.info(f"Launched {package_name} (fallback method)")
    
    def list_installed_apps(self) -> List[str]:
        """
        List all installed app package names.
        
        Returns:
            List of package names
        """
        output = self.adb.shell("pm list packages")
        packages = []
        for line in output.split("\n"):
            if line.startswith("package:"):
                packages.append(line.replace("package:", "").strip())
        return packages
    
    def force_stop(self, package_name: str):
        """
        Force stop an app.
        
        Args:
            package_name: App package name
        """
        self.adb.shell(f"am force-stop {package_name}")
        logger.info(f"Force stopped {package_name}")
    
    def clear_app_data(self, package_name: str):
        """
        Clear app data and cache.
        
        Args:
            package_name: App package name
        """
        self.adb.shell(f"pm clear {package_name}")
        logger.info(f"Cleared data for {package_name}")
    
    def get_current_app(self) -> Optional[str]:
        """
        Get currently focused app package name.
        
        Returns:
            Package name or None
        """
        try:
            output = self.adb.shell("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")
            for line in output.split("\n"):
                if "/" in line:
                    # Extract package/activity
                    parts = line.split("/")
                    if len(parts) >= 2:
                        package = parts[0].split(" ")[-1]
                        return package
        except:
            pass
        return None
