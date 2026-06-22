# PROJECT NEXUS: The "Jarvis" Architecture

## Why This Isn't Just "A Few Changes"
True "Jarvis" capability requires solving four hard problems that simple scripts ignore:
1. **Persistent Memory**: Remembering context across days, devices, and sessions.
2. **Proactive Intelligence**: Acting before being asked based on patterns.
3. **Distributed Execution**: Seamlessly moving tasks between Phone, PC, and Cloud.
4. **Self-Healing**: Detecting failures and rerouting tasks automatically.

## The Core Architecture

### 1. The Neural Core (`core/orchestrator.py`)
- **Global State Machine**: Not just a loop, but a stateful graph of execution.
- **Task Decomposition Engine**: Breaks "Plan my trip" into 15 sub-tasks across 3 devices.
- **Dynamic Resource Allocator**: Decides *where* to run code based on latency, battery, and capability.

### 2. The Hive Memory (`memory/vector_store.py` & `memory/episodic.py`)
- **Semantic Memory**: Stores facts ("User likes Italian food").
- **Episodic Memory**: Stores events ("Last Tuesday, user flew to NYC").
- **Procedural Memory**: Remembers successful task chains for faster re-execution.
- **Cross-Device Sync**: Memory is shared; phone learns what desktop knows.

### 3. The Traveling Context (`network/context_protocol.py`)
- **Serialization Protocol**: Converts complex object graphs to binary for low-latency transfer.
- **State Migration**: If your phone dies, the task state migrates to the cloud instantly.
- **Conflict Resolution**: Handles race conditions when multiple nodes try to update state.

### 4. Specialized Nodes (`nodes/`)
- **Mobile Node (Pixel 7a)**: Sensors, camera, GPS, cellular, NFC. Runs lightweight inference.
- **Desktop Node (Hermes)**: Heavy compute, file system, browser automation, local LLM.
- **Cloud Node**: Unlimited storage, heavy training, external API aggregation.

### 5. Proactive Engine (`proactive/predictor.py`)
- **Pattern Recognition**: "User always checks stocks at 9 AM" -> Pre-fetches data at 8:55 AM.
- **Anomaly Detection**: "Battery draining 2x faster than usual" -> Alerts user + runs diagnostic.
- **Intent Prediction**: Suggests actions before the prompt is finished.

## How It Works: A Real "Jarvis" Scenario

**User**: "I'm heading to the airport."

**Old System**: Sets a timer or shows maps.
**Project Nexus**:
1. **Mobile Node**: Detects movement via GPS/Accelerometer. Confirms "heading to airport" pattern.
2. **Memory**: Recalls user prefers Terminal 4, TSA PreCheck, and airline preferences.
3. **Orchestrator**: 
   - Dispatches **Mobile** to check traffic and calculate departure time.
   - Dispatches **Desktop** to check email for flight confirmation updates.
   - Dispatches **Cloud** to monitor flight status for delays.
4. **Proactive**: Notices flight is delayed. 
   - Auto-reschedules Uber (via Mobile).
   - Sends Slack message to team "Landing late" (via Desktop).
   - Updates Calendar (via Cloud).
5. **Feedback**: "Flight delayed 45 mins. Uber rescheduled. Team notified. Want to grab coffee?"

## Implementation Status
- [x] Directory Structure
- [ ] Core Orchestrator with State Graph
- [ ] Vector + Episodic Memory System
- [ ] gRPC Network Layer for Node Communication
- [ ] Mobile Node Agent (ADB + Sensor Fusion)
- [ ] Desktop Node Agent (Hermes Integration)
- [ ] Proactive Prediction Engine
- [ ] Self-Healing Mechanisms

This is a multi-week engineering effort, not a script. Let's build it right.
