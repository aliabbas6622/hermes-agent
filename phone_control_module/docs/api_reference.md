# API Reference - Phone Control Module

## PhoneController Class

### Constructor
```python
PhoneController(device_ip: Optional[str] = None, auto_connect: bool = True)
```
- `device_ip`: IP address for WiFi ADB (None for USB)
- `auto_connect`: Connect automatically on initialization

### Connection Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `connect()` | Connect to phone | `bool` |
| `disconnect()` | Disconnect from phone | `None` |
| `is_connected()` | Check connection status | `bool` |
| `get_device_info()` | Get device properties | `Dict` |

### Screen Operations

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `screenshot()` | Capture screen | `save_path` (optional) | `Image` |
| `screenshot_base64()` | Screenshot as base64 | none | `str` |
| `get_screen_elements()` | List UI elements | none | `List[Dict]` |
| `find_element()` | Find element by criteria | `text_contains`, `class_name` | `Optional[Dict]` |

### Input Operations

| Method | Description | Parameters |
|--------|-------------|------------|
| `tap(x, y)` | Tap coordinates | `x: int`, `y: int` |
| `tap_on(text)` | Tap element with text | `text_contains: str` |
| `swipe(...)` | Swipe gesture | `start_x, start_y, end_x, end_y, duration_ms` |
| `scroll(direction)` | Scroll screen | `direction: str` |
| `type_text(text)` | Type text | `text: str` |
| `press_key(code)` | Press hardware key | `key_code: int` |
| `press_home()` | Press home button | none |
| `press_back()` | Press back button | none |
| `press_recent()` | Press recent apps | none |

### App Operations

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `launch_app(pkg)` | Launch app | `package_name: str` | `None` |
| `get_current_app()` | Get focused app | none | `Optional[str]` |
| `list_apps()` | List installed apps | none | `List[str]` |

### Hermes Integration

```python
@staticmethod
get_hermes_tools() -> List[Dict]
```
Returns tool definitions for Hermes Agent registration.

---

## ADBBackend Class

Low-level ADB connection manager.

### Key Methods

- `connect_usb()` - Connect via USB
- `connect_wifi(ip)` - Connect via WiFi
- `shell(command)` - Execute shell command
- `push(local, remote)` - Upload file
- `pull(remote, local)` - Download file
- `get_device_info()` - Device properties

---

## ScreenService Class

Screen capture and UI analysis.

### Methods

- `screenshot()` → PIL Image
- `get_screen_size()` → (width, height)
- `get_ui_elements()` → List of element dicts
- `find_element(text, class)` → Element dict or None

**Element Dictionary Structure:**
```python
{
    "bounds": {"x1": int, "y1": int, "x2": int, "y2": int},
    "text": str,
    "class": str,
    "center_x": int,
    "center_y": int
}
```

---

## InputService Class

Touch and keyboard input handling.

### Methods

- `tap(x, y)` - Single tap
- `tap_element(element)` - Tap on element dict
- `swipe(x1, y1, x2, y2, duration)` - Swipe gesture
- `scroll(direction)` - Scroll (up/down/left/right)
- `type_text(text)` - Input text
- `long_press(x, y, duration)` - Long press
- `press_key(keycode)` - Hardware key

**Common Key Codes:**
- 3: HOME
- 4: BACK
- 187: APP_SWITCH
- 26: POWER
- 24/25: VOLUME UP/DOWN

---

## AppService Class

Application management.

### Methods

- `launch_app(package)` - Start app
- `list_installed_apps()` - All packages
- `force_stop(package)` - Stop app
- `clear_app_data(package)` - Clear data/cache
- `get_current_app()` - Foreground app

---

## Error Handling

All methods may raise:
- `ConnectionError` - Device not connected
- `TimeoutError` - Command timeout
- `Exception` - General errors

**Best Practice:**
```python
try:
    phone.tap(500, 500)
except ConnectionError:
    if phone.reconnect():
        phone.tap(500, 500)
```

---

## Constants

**Key Codes:**
```python
KEY_HOME = 3
KEY_BACK = 4
KEY_RECENT = 187
KEY_POWER = 26
KEY_VOLUME_UP = 24
KEY_VOLUME_DOWN = 25
```

**Directions:**
```python
SCROLL_UP = "up"
SCROLL_DOWN = "down"
SCROLL_LEFT = "left"
SCROLL_RIGHT = "right"
```
