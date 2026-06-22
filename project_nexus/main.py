"""
PROJECT NEXUS: Main Entry Point
Demonstrates the full Jarvis-like system with orchestrator, memory, 
proactive prediction, and distributed nodes working together.
"""

import asyncio
import json
import time
from core.orchestrator import orchestrator, NexusOrchestrator
from memory.hive_memory import hive_memory, MemoryType
from proactive.predictor import predictor, ProactivePredictor
from nodes.mobile_node import mobile_node, MobileNodeAgent

async def demo_jarvis_scenario():
    """
    Demonstrate a real "Jarvis" scenario:
    User says: "I'm heading to the airport"
    
    System should:
    1. Remember user preferences (terminal, airline)
    2. Check phone location and traffic
    3. Check desktop for flight emails
    4. Monitor flight status
    5. Proactively suggest actions if delays detected
    """
    
    print("=" * 60)
    print("PROJECT NEXUS: Jarvis Demo")
    print("=" * 60)
    
    # Initialize components
    print("\n[1] Initializing Nexus Core...")
    
    # Register mock executors for each node
    async def mobile_executor(task, ctx):
        print(f"   [MOBILE] Executing: {task.description}")
        await asyncio.sleep(0.5)
        
        # Simulate different results based on task
        if "location" in task.description.lower():
            return {"lat": 40.6413, "lon": -73.7781}  # Near JFK
        elif "traffic" in task.description.lower():
            return {"traffic_minutes": 25, "status": "moderate"}
        elif "battery" in task.description.lower():
            return {"level": 78, "charging": False}
        
        return f"Mobile completed: {task.description}"
    
    async def desktop_executor(task, ctx):
        print(f"   [DESKTOP] Executing: {task.description}")
        await asyncio.sleep(0.5)
        
        if "email" in task.description.lower() or "flight" in task.description.lower():
            return {"flight": "AA123", "gate": "B12", "time": "14:30", "status": "On Time"}
        
        return f"Desktop completed: {task.description}"
    
    orchestrator.register_executor("mobile_pixel7a", mobile_executor)
    orchestrator.register_executor("desktop_main", desktop_executor)
    
    # Start mobile node
    await mobile_node.connect()
    await mobile_node.start_listening()
    
    # Start proactive predictor
    predictor.start_monitoring()
    
    # Store some user memories
    print("\n[2] Loading User Memories...")
    await hive_memory.store(
        MemoryType.SEMANTIC,
        {"preference": "User prefers Terminal 4 at JFK"},
        tags=["travel", "preference"],
        importance=0.95
    )
    await hive_memory.store(
        MemoryType.SEMANTIC,
        {"preference": "User flies American Airlines"},
        tags=["travel", "airline"],
        importance=0.9
    )
    await hive_memory.learn_procedure(
        "Airport departure routine",
        [
            {"step": "check_traffic", "device": "mobile"},
            {"step": "verify_flight_status", "device": "desktop"},
            {"step": "calculate_departure_time", "device": "cloud"},
            {"step": "notify_contacts", "device": "mobile"}
        ],
        success_rate=0.98,
        execution_time=45.0
    )
    
    print(f"   Memory Stats: {hive_memory.get_stats()}")
    
    # Process the main intent
    print("\n[3] Processing Intent: 'I'm heading to the airport'")
    task_id = await orchestrator.process_intent(
        "I'm heading to the airport",
        context={"user_location": "home", "time_of_day": "afternoon"}
    )
    
    # Monitor progress
    print("\n[4] Execution Progress:")
    for i in range(15):
        status = orchestrator.get_task_status(task_id)
        
        if "nodes" in status:
            all_done = True
            for nid, info in status["nodes"].items():
                state = info["state"]
                device = info.get("device", "pending")
                desc = info["description"][:50]
                
                if state not in ["completed", "failed"]:
                    all_done = False
                
                emoji = {"completed": "✅", "executing": "⚡", "pending": "⏳", "failed": "❌"}.get(state, "⏳")
                print(f"   {emoji} [{state.upper():12}] ({device or 'pending':15}) {desc}")
            
            if all_done:
                break
        
        await asyncio.sleep(0.8)
    
    # Show proactive suggestions
    print("\n[5] Proactive Suggestions:")
    predictor.record_action("checking_travel", {"context": "airport"})
    predictor.update_metric("battery_drain_rate", 5.2)
    predictor.update_metric("battery_drain_rate", 5.1)
    predictor.update_metric("battery_drain_rate", 18.5)  # Anomaly!
    
    suggestions = await predictor.get_proactive_suggestions()
    if suggestions:
        for sug in suggestions:
            print(f"   💡 {sug['title']}: {sug['message']}")
    else:
        print("   No proactive suggestions at this time")
    
    # Recall learned procedures
    print("\n[6] Recalling Similar Past Experiences:")
    similar = await hive_memory.search_by_tags(["travel", "procedure"], limit=2)
    for mem in similar:
        if mem.memory_type == MemoryType.PROCEDURAL:
            proc = mem.content
            print(f"   📚 Learned Procedure: {proc.get('task', 'Unknown')}")
            print(f"      Success Rate: {proc.get('success_rate', 0)*100:.0f}%")
            print(f"      Avg Time: {proc.get('avg_execution_time', 0):.1f}s")
    
    # Final status
    print("\n[7] Final System Status:")
    mobile_status = mobile_node.get_status()
    print(f"   Mobile Node: {'🟢 Connected' if mobile_status['connected'] else '🔴 Disconnected'}")
    print(f"   Battery: {mobile_status['sensor_data']['battery']}%")
    print(f"   Location: {mobile_status['sensor_data']['location']}")
    
    final_status = orchestrator.get_task_status(task_id)
    completed = sum(1 for n in final_status.get("nodes", {}).values() if n["state"] == "completed")
    total = len(final_status.get("nodes", {}))
    print(f"   Tasks Completed: {completed}/{total}")
    
    # Cleanup
    predictor.stop_monitoring()
    await mobile_node.disconnect()
    mobile_node.stop_listening()
    
    print("\n" + "=" * 60)
    print("Demo Complete - Project Nexus is ready for deployment")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_jarvis_scenario())
