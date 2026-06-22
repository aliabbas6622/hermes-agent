"""
PROJECT NEXUS: Neural Core Orchestrator
"""
import asyncio
import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.orchestrator")

class TaskState(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    DECOMPOSING = "decomposing"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskNode:
    id: str
    description: str
    state: TaskState = TaskState.PENDING
    assigned_device: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionContext:
    task_id: str
    user_intent: str
    global_state: Dict[str, Any] = field(default_factory=dict)

class DeviceRegistry:
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.capabilities: Dict[str, List[str]] = defaultdict(list)
    
    def register_device(self, device_id: str, device_type: str, capabilities: List[str]):
        self.devices[device_id] = {"type": device_type, "capabilities": capabilities, "load": 0.0}
        for cap in capabilities:
            self.capabilities[cap].append(device_id)
    
    def get_best_device(self, required_caps: List[str]) -> Optional[str]:
        candidates = set(self.devices.keys())
        for cap in required_caps:
            candidates &= set(self.capabilities.get(cap, []))
        if not candidates:
            return list(self.devices.keys())[0] if self.devices else None
        return min(candidates, key=lambda d: self.devices[d]["load"])

class TaskGraph:
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
    
    def add_task(self, task: TaskNode):
        self.nodes[task.id] = task
    
    def get_ready_tasks(self) -> List[TaskNode]:
        ready = []
        for node in self.nodes.values():
            if node.state != TaskState.PENDING:
                continue
            deps_met = all(self.nodes[dep].state == TaskState.COMPLETED for dep in node.dependencies)
            if deps_met:
                ready.append(node)
        return ready

class NexusOrchestrator:
    def __init__(self):
        self.registry = DeviceRegistry()
        self.task_graphs: Dict[str, TaskGraph] = {}
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self.device_executors: Dict[str, Callable] = {}
        self._register_default_devices()
    
    def _register_default_devices(self):
        self.registry.register_device("desktop_main", "desktop", ["high_compute", "file_system", "browser"])
        self.registry.register_device("mobile_pixel7a", "mobile", ["gps", "camera", "cellular", "sensor_fusion"])
        self.registry.register_device("cloud_primary", "cloud", ["high_compute", "large_storage"])
    
    def register_executor(self, device_id: str, executor_func: Callable):
        self.device_executors[device_id] = executor_func
    
    async def process_intent(self, user_intent: str, context: Dict = None) -> str:
        task_id = str(uuid.uuid4())
        logger.info(f"Processing intent '{user_intent}' [ID: {task_id}]")
        
        exec_ctx = ExecutionContext(task_id=task_id, user_intent=user_intent, global_state=context or {})
        self.execution_contexts[task_id] = exec_ctx
        
        graph = TaskGraph()
        root_task = TaskNode(id=f"{task_id}_root", description=user_intent, state=TaskState.ANALYZING)
        graph.add_task(root_task)
        
        # Decompose immediately
        subtasks = await self._decompose_task(user_intent, root_task.id)
        for st in subtasks:
            graph.add_task(st)
            root_task.children.append(st.id)
            st.dependencies.append(root_task.id)
        
        root_task.state = TaskState.COMPLETED  # Root completes after decomposition
        root_task.result = "Decomposed into subtasks"
        
        self.task_graphs[task_id] = graph
        asyncio.create_task(self._execution_loop(task_id))
        
        return task_id
    
    async def _decompose_task(self, intent: str, parent_id: str) -> List[TaskNode]:
        subtasks = []
        if "airport" in intent.lower() or "travel" in intent.lower():
            subtasks = [
                TaskNode(id=str(uuid.uuid4()), description="Check current location and traffic to airport", metadata={"required_caps": ["gps", "cellular"]}),
                TaskNode(id=str(uuid.uuid4()), description="Fetch flight status from email/calendar", metadata={"required_caps": ["file_system", "browser"]}),
                TaskNode(id=str(uuid.uuid4()), description="Calculate optimal departure time", metadata={"required_caps": ["high_compute"]}),
                TaskNode(id=str(uuid.uuid4()), description="Notify contacts of ETA", metadata={"required_caps": ["cellular"]})
            ]
            subtasks[2].dependencies = [subtasks[0].id, subtasks[1].id]
            subtasks[3].dependencies = [subtasks[2].id]
        elif "battery" in intent.lower() or "info" in intent.lower():
            subtasks = [
                TaskNode(id=str(uuid.uuid4()), description="Get battery level from mobile", metadata={"required_caps": ["sensor_fusion"]}),
                TaskNode(id=str(uuid.uuid4()), description="Log battery stats", metadata={"required_caps": ["file_system"]})
            ]
        else:
            subtasks = [TaskNode(id=str(uuid.uuid4()), description=f"Execute: {intent}", metadata={"required_caps": ["high_compute"]})]
        return subtasks
    
    async def _execution_loop(self, task_id: str):
        graph = self.task_graphs.get(task_id)
        if not graph:
            return
        
        while task_id in self.task_graphs:
            ready_tasks = graph.get_ready_tasks()
            
            if not ready_tasks:
                all_done = all(n.state in [TaskState.COMPLETED, TaskState.FAILED] for n in graph.nodes.values())
                if all_done:
                    logger.info(f"Task graph {task_id} completed")
                    break
                await asyncio.sleep(0.3)
                continue
            
            # Execute ready tasks in parallel
            await asyncio.gather(*[self._execute_task(task_id, task) for task in ready_tasks], return_exceptions=True)
    
    async def _execute_task(self, task_id: str, task: TaskNode):
        task.state = TaskState.EXECUTING
        required_caps = task.metadata.get("required_caps", [])
        best_device = self.registry.get_best_device(required_caps)
        task.assigned_device = best_device or "unknown"
        
        logger.info(f"Executing '{task.description[:40]}...' on {task.assigned_device}")
        
        executor = self.device_executors.get(task.assigned_device)
        if executor:
            try:
                result = await executor(task, self.execution_contexts[task_id])
                task.result = result
                task.state = TaskState.COMPLETED
            except Exception as e:
                task.retry_count += 1
                if task.retry_count >= task.max_retries:
                    task.state = TaskState.FAILED
                    task.error = str(e)
                else:
                    task.state = TaskState.PENDING  # Retry
        else:
            await asyncio.sleep(0.5)  # Simulate
            task.result = f"Simulated result on {task.assigned_device}"
            task.state = TaskState.COMPLETED
    
    def get_task_status(self, task_id: str) -> Dict:
        graph = self.task_graphs.get(task_id)
        if not graph:
            return {"error": "Task not found"}
        return {
            "task_id": task_id,
            "nodes": {nid: {"description": n.description, "state": n.state.value, "device": n.assigned_device, "result": n.result, "error": n.error} for nid, n in graph.nodes.items()}
        }

orchestrator = NexusOrchestrator()
