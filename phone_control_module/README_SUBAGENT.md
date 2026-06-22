# Mobile Sub-Agent for Hermes Agent

A specialized autonomous sub-agent designed to control Android devices (specifically optimized for Google Pixel 7a on Android 16) when delegated tasks by the main Hermes Agent.

## Architecture Overview

```
Main Hermes Agent
       │
       │ (Delegates high-level goal)
       ▼
Mobile Sub-Agent (This Module)
       │
       ├── Planning Layer (Breaks goals into steps)
       ├── Perception Layer (Analyzes screen via OCR/CV)
       └── Execution Layer (ADB Commands: Tap, Swipe, Type)
```

## Features

- **Autonomous Execution**: Receives a natural language goal (e.g., "Send a WhatsApp message to John") and autonomously plans and executes the necessary steps.
- **Visual Perception**: Analyzes screen contents to identify buttons, text, and UI elements dynamically.
- **State Management**: Tracks task progress, handles errors, and verifies completion.
- **Seamless Integration**: Exposes standard tools (`delegate_mobile_task`, `check_mobile_status`) that plug directly into the Hermes Agent tool system.

## Installation

1. **Prerequisites**:
   - Python 3.11+
   - Google Pixel 7a (Android 16) with USB Debugging enabled.
   - ADB installed on your system.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # Note: Add opencv-python, easyocr, pillow to requirements.txt if using full visual features
   ```

3. **Setup Device**:
   Connect your phone via USB once to authorize, then run the setup script from the parent module:
   ```bash
   python setup_device.py
   ```

## Usage with Hermes Agent

### 1. Initialize Integration

In your main Hermes Agent startup script (e.g., `run_agent.py` or `cli.py`):

```python
from phone_control_module.hermes_integration import register_with_hermes, MOBILE_AGENT_SYSTEM_PROMPT

# Assuming 'agent' is your instantiated Hermes Agent object
device_ip = "192.168.1.50:5555"  # Your Pixel 7a wireless ADB address

# Register the tools
mobile_integration = register_with_hermes(agent, device_id=device_ip)

# Update system prompt (Optional but recommended)
# Depending on how Hermes handles prompts, you might append this to the system message
agent.system_prompt += "\n\n" + MOBILE_AGENT_SYSTEM_PROMPT
```

### 2. Delegate Tasks

Once integrated, you can simply ask Hermes:
> "Hey Hermes, check my phone battery and send a text to Alice saying I'm running late."

Hermes will internally call:
```json
{
  "tool": "delegate_mobile_task",
  "arguments": {
    "goal": "Check battery level and send SMS to Alice: 'I'm running late'"
  }
}
```

The Mobile Sub-Agent will then:
1. Connect to the device.
2. Plan the steps (Open Settings -> Check Battery OR Open Messages -> Find Alice -> Type -> Send).
3. Execute actions while analyzing the screen.
4. Report success/failure back to Hermes.

## Directory Structure

```
phone_control_module/
├── __init__.py
├── backend/
│   └── adb_controller.py      # Low-level ADB communication
├── services/
│   ├── screen_service.py      # Screenshot handling
│   ├── input_service.py       # Tap, Swipe, Type
│   └── app_service.py         # App launching/management
├── mobile_agent_core.py       # THE SUB-AGENT LOGIC (Planning, State, Execution Loop)
├── visual_perception.py       # Screen analysis (OCR, UI Detection)
├── hermes_integration.py      # Tools & Prompts for Hermes
├── setup_device.py            # Wireless ADB setup wizard
└── README.md                  # This file
```

## Configuration for Pixel 7a (Android 16)

The module is pre-configured for Pixel 7a specifics:
- **Resolution**: Handled dynamically, defaults to 1080x2400 logic.
- **Permissions**: Android 16 may require specific ADB permissions for secure settings. The setup script handles `adb shell pm grant` for necessary permissions if possible.
- **Wireless Debugging**: Optimized for persistent wireless connection on local network.

## Advanced: Customizing the Agent Behavior

### Modifying the Planner
Edit `mobile_agent_core.py` -> `_plan_workflow()`. 
Currently uses simple heuristics. For production, replace this with an LLM call to generate the step list dynamically based on the goal.

### Enhancing Vision
Edit `visual_perception.py`. 
Currently a placeholder. Integrate **EasyOCR** for text reading or a fine-tuned **YOLO** model for UI element detection to make the agent truly robust.

## Troubleshooting

- **"Device unauthorized"**: Check your phone screen for the RSA key fingerprint prompt and accept it.
- **"Connection refused"**: Ensure wireless debugging is enabled and the IP address is correct. Restart ADB: `adb kill-server && adb start-server`.
- **"Permission denied"**: Some actions (like changing system settings) may require root or special ADB permissions on Android 16.

## Security Note

This agent has full control over your device. Only delegate tasks from trusted sources. Do not expose the ADB port (5555) to the public internet without firewall protection.
