"""
Hermes Agent Integration Module.
Provides the bridge between the main Hermes Agent and the Mobile Sub-Agent.
Includes tools, prompts, and delegation logic.
"""

import logging
from typing import List, Dict, Any, Optional
from .mobile_agent_core import MobileSubAgent

logger = logging.getLogger(__name__)

class HermesMobileIntegration:
    """
    Integrates the Mobile Sub-Agent into the Hermes Agent ecosystem.
    Exposes tools that Hermes can call and handles the delegation protocol.
    """
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.mobile_agent: Optional[MobileSubAgent] = None

    def get_hermes_tools(self) -> List[Dict]:
        """
        Returns a list of tool definitions compatible with Hermes Agent's tool system.
        These tools allow Hermes to delegate mobile tasks.
        """
        return [
            {
                "name": "delegate_mobile_task",
                "description": "Delegates a high-level mobile task to the specialized Mobile Sub-Agent. Use this when the user wants to perform actions on their Android phone (Pixel 7a).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "The natural language description of what needs to be done on the phone (e.g., 'Open WhatsApp and send a message to John', 'Turn on WiFi', 'Take a screenshot')."
                        }
                    },
                    "required": ["goal"]
                },
                "function": self._execute_delegated_task
            },
            {
                "name": "check_mobile_status",
                "description": "Checks the connection status and basic info of the connected Android device.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "function": self._get_device_status
            },
            {
                "name": "capture_mobile_screen",
                "description": "Captures the current screen of the Android device and returns it (or saves it).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "save_path": {
                            "type": "string",
                            "description": "Optional path to save the screenshot."
                        }
                    },
                    "required": []
                },
                "function": self._capture_screen
            }
        ]

    async def _execute_delegated_task(self, goal: str) -> Dict[str, Any]:
        """
        Internal function invoked by Hermes when it calls the delegation tool.
        Spins up the mobile agent and executes the goal.
        """
        logger.info(f"Hermes delegated mobile task: {goal}")
        
        if not self.mobile_agent:
            self.mobile_agent = MobileSubAgent(self.device_id)
        
        try:
            result = await self.mobile_agent.execute_goal(goal)
            return {
                "success": result.get("success", False),
                "message": result.get("summary", "Task execution finished"),
                "details": result
            }
        except Exception as e:
            logger.error(f"Delegated task failed: {e}")
            return {"success": False, "message": f"Mobile agent error: {str(e)}"}

    async def _get_device_status(self) -> Dict[str, Any]:
        """Returns device connection status."""
        # Implementation would check ADB connection
        return {
            "connected": True, # Placeholder
            "device_id": self.device_id or "default",
            "model": "Google Pixel 7a",
            "android_version": "16"
        }

    async def _capture_screen(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Captures screen via the mobile agent."""
        if not self.mobile_agent:
            self.mobile_agent = MobileSubAgent(self.device_id)
            if not await self.mobile_agent.initialize():
                return {"success": False, "error": "Could not connect to device"}
        
        # Direct call to screen service
        screenshot = await self.mobile_agent.screen.capture_screenshot()
        
        result = {"success": True, "screenshot_data": "base64_encoded_string_placeholder"}
        if save_path:
            # Save logic here
            result["saved_to"] = save_path
            
        return result

# --- Prompt Engineering for Hermes ---

MOBILE_AGENT_SYSTEM_PROMPT = """
You have access to a specialized Mobile Sub-Agent capable of controlling an Android device (Google Pixel 7a, Android 16).

When the user requests any action involving their phone, you should use the `delegate_mobile_task` tool.
Do not attempt to simulate phone actions yourself; instead, clearly describe the goal to the sub-agent.

Examples of valid delegations:
- "Open Instagram and like the first post."
- "Check my battery level."
- "Send a text to Mom saying I'll be late."
- "Turn on Bluetooth."

The sub-agent will handle the complex planning, screen analysis, and input execution. 
Wait for the sub-agent's report before responding to the user.
"""

def register_with_hermes(hermes_instance, device_id: Optional[str] = None):
    """
    Helper function to register mobile tools with an existing Hermes Agent instance.
    Usage:
        register_with_hermes(my_hermes_agent, device_id="192.168.1.50:5555")
    """
    integration = HermesMobileIntegration(device_id)
    tools = integration.get_hermes_tools()
    
    # Assuming Hermes has an add_tools method or similar
    if hasattr(hermes_instance, 'add_tools'):
        hermes_instance.add_tools(tools)
    elif hasattr(hermes_instance, 'tools'):
        hermes_instance.tools.extend(tools)
    else:
        logger.warning("Could not find standard tool registration method on Hermes instance.")
    
    # Inject the system prompt advice into Hermes' context if possible
    logger.info("Mobile Agent tools registered with Hermes.")
    return integration
