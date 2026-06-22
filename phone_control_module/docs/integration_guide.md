# Hermes Agent Phone Control Integration Guide

## Overview

This module adds Android phone control capabilities to Hermes Agent, allowing the AI to:
- View your phone screen in real-time
- Tap, swipe, and type on your phone
- Launch and manage apps
- Read UI elements for intelligent interaction

Optimized for **Google Pixel 7a (Android 16)** but works with most Android devices.

## Installation

### Step 1: Install Dependencies

```bash
cd /workspace/phone_control_module
pip install -r requirements.txt
```

### Step 2: Set Up Your Phone

**On your Pixel 7a:**

1. **Enable Developer Options:**
   - Settings → About phone
   - Tap "Build number" 7 times
   - Enter PIN when prompted

2. **Enable USB Debugging:**
   - Settings → System → Developer options
   - Toggle "USB debugging" ON

3. **Enable Wireless Debugging:**
   - Settings → System → Developer options
   - Toggle "Wireless debugging" ON
   - Note your IP address (shown under wireless debugging)

### Step 3: Initial Connection (USB Required)

```bash
# Connect phone via USB first
python setup_device.py
```

Follow the prompts to:
- Accept RSA key authorization on your phone
- Enable wireless ADB
- Save your device IP

After this one-time setup, you can disconnect USB!

## Integration with Hermes Agent

### Method 1: Register as Tools

Add this to your Hermes Agent initialization code:

```python
from phone_control_module.src import PhoneController

# Initialize phone controller
phone = PhoneController(device_ip="192.168.1.100")

# Get tool definitions
tools = PhoneController.get_hermes_tools()

# Register tools with Hermes Agent
for tool_def in tools:
    agent.register_tool(tool_def, execute_phone_tool)

def execute_phone_tool(tool_name, params):
    """Execute phone control tool."""
    if tool_name == "phone_screenshot":
        return {"image": phone.screenshot_base64()}
    elif tool_name == "phone_tap":
        if "text" in params:
            success = phone.tap_on(params["text"])
            return {"success": success}
        else:
            phone.tap(params["x"], params["y"])
            return {"success": True}
    # ... implement other tools
```

### Method 2: Create Custom Skill

Create a skill file in `hermes_agent/skills/`:

```python
# phone_control_skill.py
from phone_control_module.src import PhoneController

class PhoneControlSkill:
    def __init__(self):
        self.phone = PhoneController(device_ip="192.168.1.100")
    
    def execute(self, action: str, **kwargs):
        """Execute phone action."""
        if action == "screenshot":
            return self.phone.screenshot_base64()
        elif action == "tap":
            return self.phone.tap(kwargs.get("x"), kwargs.get("y"))
        # ... etc
```

## Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `phone_screenshot` | Capture screen | `save_path` (optional) |
| `phone_tap` | Tap coordinates or element | `x`, `y` OR `text` |
| `phone_swipe` | Swipe gesture | `start_x`, `start_y`, `end_x`, `end_y`, `duration_ms` |
| `phone_type` | Type text | `text` |
| `phone_launch_app` | Open app | `package` |
| `phone_get_elements` | List UI elements | none |
| `phone_press_key` | Hardware button | `key` (home/back/recent/power) |
| `phone_scroll` | Scroll screen | `direction` (up/down/left/right) |

## Example Usage Scenarios

### 1. Send WhatsApp Message

```python
phone.launch_app("com.whatsapp")
phone.tap_on("New chat")
phone.type_text("John Doe")
phone.tap_on("John Doe")
phone.type_text("Hello from Hermes Agent!")
phone.press_key(3)  # Home
```

### 2. Check Notifications

```python
phone.swipe(540, 100, 540, 2000)  # Pull down notification shade
elements = phone.get_screen_elements()
notifications = [e for e in elements if "notification" in e.get("class", "").lower()]
```

### 3. Navigate Settings

```python
phone.launch_app("com.android.settings")
phone.tap_on("Network")
phone.scroll("down")
phone.tap_on("WiFi")
```

## Security Considerations

⚠️ **Important:**

1. **Authorization Required**: First connection needs USB + RSA key approval
2. **Network Security**: Only use on trusted WiFi networks
3. **Audit Logging**: All actions are logged by Hermes Agent
4. **User Approval**: Configure Hermes Agent to require approval for phone actions
5. **Disable When Not In Use**: Turn off wireless debugging when done

## Troubleshooting

### Device Not Connecting

```bash
# Check ADB status
adb devices

# Restart ADB server
adb kill-server
adb start-server

# Reconnect
adb connect 192.168.1.100:5555
```

### Permission Denied

- Revoke USB debugging authorizations on phone
- Re-enable USB debugging
- Re-run `setup_device.py`

### High Latency

- Use 5GHz WiFi network
- Move closer to router
- Reduce screen resolution temporarily:
  ```bash
  adb shell wm size 720x1600
  # Reset: adb shell wm size reset
  ```

## Advanced Configuration

### Multiple Devices

```python
# Connect to multiple phones
phone1 = PhoneController(device_ip="192.168.1.100")
phone2 = PhoneController(device_ip="192.168.1.101")
```

### Custom ADB Port

```python
phone = PhoneController(device_ip="192.168.1.100", port=5556)
```

### Manual Connection Control

```python
phone = PhoneController(device_ip="192.168.1.100", auto_connect=False)
# Later...
success = phone.connect()
```

## API Reference

See `src/controller.py` for complete API documentation.

## Support

For issues specific to Pixel 7a or Android 16:
- Check Android Developer documentation
- Review ADB troubleshooting guides
- Verify wireless debugging settings

## License

MIT License - Same as Hermes Agent main repository
