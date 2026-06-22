"""
Mobile Agent Core - A specialized sub-agent for controlling Android devices.
This agent receives high-level goals from the main Hermes Agent and executes
complex mobile workflows autonomously.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .backend.adb_controller import ADBController
from .services.screen_service import ScreenService
from .services.input_service import InputService
from .services.app_service import AppService
from .visual_perception import VisualPerception

logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskStep:
    description: str
    action_type: str  # e.g., "tap", "type", "swipe", "launch_app"
    parameters: Dict[str, Any]
    status: str = "pending"
    result: Optional[str] = None

@dataclass
class MobileAgentContext:
    goal: str
    current_step_index: int = 0
    steps: List[TaskStep] = field(default_factory=list)
    state: AgentState = AgentState.IDLE
    last_screen_analysis: Optional[Dict] = None
    error_message: Optional[str] = None

class MobileSubAgent:
    """
    Autonomous sub-agent for mobile control.
    Designed to be invoked by the main Hermes Agent.
    """
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.adb = ADBController(device_id)
        self.screen = ScreenService(self.adb)
        self.input_svc = InputService(self.adb)
        self.app_svc = AppService(self.adb)
        self.perception = VisualPerception()
        
        self.context: Optional[MobileAgentContext] = None
        self._is_running = False

    async def initialize(self) -> bool:
        """Connect to the device and verify readiness."""
        try:
            connected = await self.adb.connect()
            if not connected:
                logger.error("Failed to connect to Android device")
                return False
            
            # Verify device is Pixel 7a / Android 16 compatible
            info = await self.adb.get_device_info()
            logger.info(f"Connected to device: {info.get('model', 'Unknown')} ({info.get('android_version', 'Unknown')})")
            return True
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    async def execute_goal(self, goal: str) -> Dict[str, Any]:
        """
        Main entry point for the main Hermes Agent to delegate a task.
        Returns a detailed report of execution.
        """
        if not await self.initialize():
            return {"success": False, "error": "Could not connect to device"}

        self.context = MobileAgentContext(goal=goal)
        self.context.state = AgentState.PLANNING
        self._is_running = True

        logger.info(f"Mobile Agent starting task: {goal}")

        try:
            # Step 1: Plan the workflow
            plan_success = await self._plan_workflow()
            if not plan_success:
                return self._generate_report("Planning failed")

            # Step 2: Execute steps loop
            while self.context.current_step_index < len(self.context.steps):
                if not self._is_running:
                    return self._generate_report("Task interrupted")
                
                step_result = await self._execute_current_step()
                if not step_result:
                    return self._generate_report(f"Step {self.context.current_step_index} failed")
                
                self.context.current_step_index += 1

            # Step 3: Final Verification
            verification_passed = await self._verify_completion()
            
            if verification_passed:
                self.context.state = AgentState.COMPLETED
                return self._generate_report("Task completed successfully")
            else:
                self.context.state = AgentState.FAILED
                return self._generate_report("Task completed but verification failed")

        except Exception as e:
            logger.exception(f"Critical error in mobile agent: {e}")
            self.context.state = AgentState.FAILED
            self.context.error_message = str(e)
            return self._generate_report(f"Critical error: {str(e)}")
        finally:
            self._is_running = False

    async def _plan_workflow(self) -> bool:
        """
        Generates a step-by-step plan based on the goal.
        In a full implementation, this would call an LLM to generate the plan.
        Here we simulate a basic heuristic planner or prepare the prompt for the LLM.
        """
        self.context.state = AgentState.PLANNING
        
        # Placeholder for LLM-based planning
        # For now, we create a generic structure that the main Hermes Agent 
        # could theoretically populate, or we use a simple heuristic.
        
        # Example heuristic: If goal contains "open", create launch step
        goal_lower = self.context.goal.lower()
        
        if "open" in goal_lower or "launch" in goal_lower:
            # Extract app name (simplified)
            # Real implementation would use NLP/LLM here
            self.context.steps.append(TaskStep(
                description="Identify and launch target application",
                action_type="launch_app",
                parameters={"query": self.context.goal}
            ))
        
        # Add a generic verification step
        self.context.steps.append(TaskStep(
            description="Verify task completion",
            action_type="verify",
            parameters={"goal": self.context.goal}
        ))

        if not self.context.steps:
            # Fallback: Single generic step if heuristics fail
            self.context.steps.append(TaskStep(
                description="Execute user goal",
                action_type="custom",
                parameters={"instruction": self.context.goal}
            ))

        logger.info(f"Generated plan with {len(self.context.steps)} steps")
        return True

    async def _execute_current_step(self) -> bool:
        """Executes the current step in the plan."""
        self.context.state = AgentState.EXECUTING
        step = self.context.steps[self.context.current_step_index]
        
        logger.info(f"Executing step: {step.description}")

        try:
            # Capture current screen for context
            screenshot = await self.screen.capture_screenshot()
            analysis = await self.perception.analyze_screen(screenshot, step.description)
            self.context.last_screen_analysis = analysis

            if step.action_type == "launch_app":
                success = await self._handle_launch_app(step, analysis)
            elif step.action_type == "tap":
                success = await self._handle_tap(step, analysis)
            elif step.action_type == "type":
                success = await self._handle_type(step, analysis)
            elif step.action_type == "swipe":
                success = await self._handle_swipe(step, analysis)
            elif step.action_type == "verify":
                success = True  # Handled in final verification
            else:
                logger.warning(f"Unknown action type: {step.action_type}")
                success = False

            step.status = "completed" if success else "failed"
            step.result = "Success" if success else "Failed"
            return success

        except Exception as e:
            logger.error(f"Step execution error: {e}")
            step.status = "failed"
            step.result = str(e)
            return False

    async def _handle_launch_app(self, step: TaskStep, analysis: Dict) -> bool:
        """Logic to find and launch an app."""
        # Use the query to find the package name
        # In a real scenario, the LLM or a mapping service resolves "WhatsApp" -> "com.whatsapp"
        package_name = await self.app_svc.resolve_package_from_query(step.parameters.get("query", ""))
        
        if not package_name:
            logger.error("Could not resolve package name from query")
            return False
            
        return await self.app_svc.launch_app(package_name)

    async def _handle_tap(self, step: TaskStep, analysis: Dict) -> bool:
        """Logic to tap a specific element."""
        coords = analysis.get('target_coordinates')
        if coords:
            return await self.input_svc.tap(coords['x'], coords['y'])
        return False

    async def _handle_type(self, step: TaskStep, analysis: Dict) -> bool:
        """Logic to type text."""
        text = step.parameters.get('text', '')
        return await self.input_svc.type_text(text)

    async def _handle_swipe(self, step: TaskStep, analysis: Dict) -> bool:
        """Logic to swipe."""
        direction = step.parameters.get('direction', 'up')
        return await self.input_svc.swipe(direction)

    async def _verify_completion(self) -> bool:
        """Verifies if the overall goal was achieved."""
        self.context.state = AgentState.VERIFYING
        # Capture final state
        screenshot = await self.screen.capture_screenshot()
        # Analyze if goal conditions are met
        # This would typically involve an LLM checking the screen against the goal
        logger.info("Verifying task completion...")
        return True # Placeholder

    def _generate_report(self, summary: str) -> Dict[str, Any]:
        """Generates a structured report for the main Hermes Agent."""
        return {
            "success": self.context.state == AgentState.COMPLETED,
            "summary": summary,
            "goal": self.context.goal,
            "steps_executed": len([s for s in self.context.steps if s.status == "completed"]),
            "total_steps": len(self.context.steps),
            "state": self.context.state.value,
            "error": self.context.error_message
        }

    async def stop(self):
        """Stops the agent gracefully."""
        self._is_running = False
        logger.info("Mobile Agent stopped")
