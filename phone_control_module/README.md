# Android Phone Control Module for Hermes Agent

Control your Google Pixel 7a (Android 16) directly from Hermes Agent.

## Quick Start

### Prerequisites
1. **Enable Developer Options** on your Pixel 7a:
   - Go to Settings → About phone
   - Tap "Build number" 7 times
   - Enter your PIN when prompted

2. **Enable USB Debugging**:
   - Settings → System → Developer options
   - Toggle "USB debugging" ON

3. **Enable Wireless Debugging** (for WiFi control):
   - Settings → System → Developer options
   - Toggle "Wireless debugging" ON
   - Note your device IP address

### Installation

```bash
cd /workspace/phone_control_module
pip install -r requirements.txt
```

### Initial Setup (USB Required First Time)

1. Connect your Pixel 7a via USB
2. Run the setup script:
```bash
python setup_device.py --wireless
```
3. Accept the RSA key fingerprint prompt on your phone
4. Disconnect USB - now works over WiFi!

## Usage

### Basic Commands

```python
from phone_control import PhoneController

# Initialize controller
phone = PhoneController(device_ip="192.168.1.100")

# Take a screenshot
screenshot = phone.screenshot()
screenshot.save("current_screen.png")

# Tap at coordinates
phone.tap(500, 1000)

# Swipe gesture
phone.swipe(start_x=500, start_y=1500, end_x=500, end_y=500)

# Type text
phone.type_text("Hello World")

# Launch an app
phone.launch_app("com.whatsapp")

# Get current screen UI elements
elements = phone.get_ui_elements()
for elem in elements:
    print(f"{elem['text']} at {elem['bounds']}")
```

### Integration with Hermes Agent

The module automatically registers as a tool category:

- `phone_screenshot` - Capture current screen
- `phone_tap` - Tap at location or on UI element
- `phone_swipe` - Perform swipe gesture
- `phone_type` - Input text
- `phone_launch_app` - Open application
- `phone_get_elements` - Analyze screen content
- `phone_press_key` - Hardware button simulation (Home, Back, etc.)

## Features

✅ **Screen Control**
- Real-time screenshot capture
- UI element detection and analysis
- Coordinate-based and element-based interaction

✅ **Input Methods**
- Tap, long press, double tap
- Swipe, scroll gestures
- Text input (English + special characters)
- Key events (Home, Back, Recent, Power, Volume)

✅ **App Management**
- Launch apps by package name
- List installed apps
- Force stop apps
- Clear app data/cache

✅ **Connection**
- USB debugging support
- WiFi ADB (persistent connection)
- Auto-reconnect on disconnect
- Multi-device support

## Security

⚠️ **Important Security Notes**:
- All phone actions require explicit approval in Hermes Agent
- Connection logs are maintained for audit
- RSA key authorization required on first connection
- No root access needed - uses standard ADB protocols
- Disable wireless debugging when not in use

## Troubleshooting

### Device Not Found
```bash
# Check connection
adb devices

# Restart ADB server
adb kill-server
adb start-server

# Reconnect wirelessly
adb connect <device_ip>:5555
```

### Permission Denied
- Ensure USB debugging is enabled
- Revoke USB debugging authorizations and re-authorize
- Check that wireless debugging is active

### High Latency
- Use 5GHz WiFi network
- Reduce screen resolution if needed
- Ensure strong WiFi signal

## API Reference

See `docs/api_reference.md` for complete API documentation.

## Examples

Check the `examples/` directory for:
- Automated messaging workflows
- Screen monitoring scripts
- App automation templates
- Custom skill examples

## License

MIT License - See main Hermes Agent repository
