"""
Jarvis Core - Main Orchestration Engine
Integrates all components: Event Bus, Memory, Daemons, and Device Control.
Provides unified API for the main Hermes agent to interact with the system.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import core components
from jarvis_core.events.event_bus import TokenEfficientEventBus, Event, Priority, setup_default_handlers
from jarvis_core.memory.hermes_bridge import HermesMemoryBridge
from jarvis_core.daemons.background_intelligence import DaemonManager
from jarvis_core.quant.turbo_quant import TurboQuantEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.core")

@dataclass
class SystemConfig:
    """Configuration for the Jarvis Core system."""
    memory_db_path: str = "jarvis_memory.db"
    embedding_dim: int = 768
    enable_daemons: bool = True
    log_efficiency_stats: bool = True
    stats_interval_seconds: int = 60

class JarvisCore:
    """
    Central orchestration engine that ties together:
    - Token-efficient event processing
    - Compressed vector memory
    - Background intelligence daemons
    - Multi-device coordination
    
    This is the "brain stem" that handles automatic functions,
    leaving the main Hermes agent free for complex reasoning.
    """
    
    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        self.running = False
        
        logger.info("Initializing Jarvis Core...")
        
        # 1. Initialize Event Bus (token-efficient filtering)
        self.event_bus = TokenEfficientEventBus()
        setup_default_handlers(self.event_bus)
        
        # 2. Initialize Memory Bridge (TurboQuant compression)
        self.memory = HermesMemoryBridge(
            db_path=self.config.memory_db_path,
            embedding_dim=self.config.embedding_dim
        )
        
        # 3. Initialize Daemon Manager (background intelligence)
        if self.config.enable_daemons:
            self.daemon_manager = DaemonManager(
                event_bus=self.event_bus,
                memory_bridge=self.memory
            )
        else:
            self.daemon_manager = None
            
        # 4. Register internal event handlers
        self._register_internal_handlers()
        
        logger.info("Jarvis Core initialized successfully")
        
    def _register_internal_handlers(self):
        """Register handlers for internal event processing."""
        
        def on_critical_event(event: Event):
            """Handle critical events immediately."""
            logger.warning(f"CRITICAL EVENT: {event.content}")
            # Store in memory with high importance
            self.memory.store(
                content=event.content,
                category="critical_event",
                importance=0.95,
                metadata=event.metadata
            )
            
        def on_medium_event(event: Event):
            """Handle medium priority events."""
            # Store with moderate importance
            self.memory.store(
                content=event.content,
                category=event.category,
                importance=0.5,
                metadata=event.metadata
            )
            
        def on_low_event(event: Event):
            """Handle low priority batched events."""
            # Just log, don't store individually
            pass
            
        self.event_bus.register_handler(Priority.CRITICAL, on_critical_event)
        self.event_bus.register_handler(Priority.HIGH, on_critical_event)
        self.event_bus.register_handler(Priority.MEDIUM, on_medium_event)
        self.event_bus.register_handler(Priority.LOW, on_low_event)
        
    def start(self):
        """Start the Jarvis Core system."""
        if self.running:
            logger.warning("Jarvis Core already running")
            return
            
        self.running = True
        
        # Start background daemons
        if self.daemon_manager:
            self.daemon_manager.start_all()
            logger.info("Background daemons started")
            
        # Start efficiency monitoring
        if self.config.log_efficiency_stats:
            self._start_stats_monitoring()
            
        logger.info("Jarvis Core is now running")
        
    def stop(self):
        """Stop the Jarvis Core system gracefully."""
        self.running = False
        
        if self.daemon_manager:
            self.daemon_manager.stop_all()
            
        logger.info("Jarvis Core stopped")
        
    def _start_stats_monitoring(self):
        """Start periodic efficiency statistics logging."""
        import threading
        
        def monitor_loop():
            while self.running:
                time.sleep(self.config.stats_interval_seconds)
                if self.running:
                    self._log_efficiency_stats()
                    
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
    def _log_efficiency_stats(self):
        """Log current efficiency statistics."""
        stats = self.event_bus.get_efficiency_report()
        mem_stats = self.memory.get_stats()
        
        logger.info(
            f"Efficiency Report: "
            f"{stats['total_events']} events processed, "
            f"{stats['llm_calls_avoided']} LLM calls avoided "
            f"({stats['filter_efficiency_percent']}% efficiency), "
            f"Estimated token savings: {stats['estimated_token_savings']:,}"
        )
        
        logger.debug(
            f"Memory Stats: "
            f"{mem_stats['total_memories']} memories stored, "
            f"Compression ratio: {mem_stats['quant_compression_ratio']:.1f}x, "
            f"Storage: {mem_stats['quant_storage_kb']:.2f} KB"
        )
        
    # ========== Public API for Hermes Agent ==========
    
    def publish_event(self, source: str, category: str, content: str,
                     priority: str = "medium", metadata: Dict = None) -> bool:
        """
        Publish an event to the system.
        
        Args:
            source: Event source (e.g., "android_phone", "file_watcher")
            category: Event category (e.g., "notification", "system_alert")
            content: Event content/text
            priority: "trivial", "low", "medium", "high", "critical"
            metadata: Additional event data
            
        Returns:
            True if LLM call was triggered, False if handled automatically
        """
        priority_map = {
            "trivial": Priority.TRIVIAL,
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL
        }
        
        event = Event(
            source=source,
            category=category,
            content=content,
            priority=priority_map.get(priority.lower(), Priority.MEDIUM),
            metadata=metadata or {}
        )
        
        llm_needed = self.event_bus.publish(event)
        return llm_needed
    
    def query_memory(self, query: str, top_k: int = 5,
                    category_filter: str = None) -> List[Dict]:
        """
        Query the memory system for relevant context.
        
        Args:
            query: Search query
            top_k: Number of results
            category_filter: Optional category filter
            
        Returns:
            List of relevant memory entries
        """
        return self.memory.retrieve_relevant(
            query=query,
            top_k=top_k,
            category_filter=category_filter
        )
    
    def get_context_for_topic(self, topic: str, max_tokens: int = 2000) -> str:
        """
        Get optimized context window for a specific topic.
        Use this before calling the LLM to provide relevant history.
        
        Args:
            topic: Current topic/task
            max_tokens: Maximum token budget
            
        Returns:
            Formatted context string
        """
        return self.memory.get_context_window(
            current_topic=topic,
            max_tokens=max_tokens
        )
    
    def learn_from_interaction(self, content: str, category: str = "interaction",
                               importance: float = 0.5, metadata: Dict = None):
        """
        Store a learning from user interaction.
        
        Args:
            content: What was learned
            category: Type of learning
            importance: How important this is (0.0-1.0)
            metadata: Additional data
        """
        self.memory.store(
            content=content,
            category=category,
            importance=importance,
            metadata=metadata
        )
        
    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        status = {
            'running': self.running,
            'event_bus': self.event_bus.get_efficiency_report(),
            'memory': self.memory.get_stats(),
        }
        
        if self.daemon_manager:
            status['daemons'] = self.daemon_manager.get_status()
            
        return status
    
    # ========== Convenience Methods ==========
    
    def notify(self, message: str, source: str = "system"):
        """Send a notification through the event bus."""
        self.publish_event(
            source=source,
            category="notification",
            content=message,
            priority="medium"
        )
        
    def alert(self, message: str, source: str = "system"):
        """Send a critical alert through the event bus."""
        self.publish_event(
            source=source,
            category="alert",
            content=message,
            priority="critical"
        )
        
    def remember(self, fact: str, category: str = "fact"):
        """Store a fact in long-term memory."""
        self.learn_from_interaction(
            content=fact,
            category=category,
            importance=0.7
        )


# ========== Factory Function ==========

def create_jarvis_core(config: SystemConfig = None) -> JarvisCore:
    """
    Factory function to create and initialize Jarvis Core.
    
    Usage:
        jarvis = create_jarvis_core()
        jarvis.start()
        
        # Now use jarvis throughout your application
        jarvis.notify("System ready")
        jarvis.remember("User prefers dark mode")
    """
    return JarvisCore(config=config)


# ========== Example Usage ==========

if __name__ == "__main__":
    # Create and start Jarvis Core
    jarvis = create_jarvis_core()
    jarvis.start()
    
    try:
        # Simulate some events
        jarvis.notify("Welcome to Jarvis Core!")
        jarvis.remember("User has Pixel 7a with Android 16")
        jarvis.learn_from_interaction(
            "User works best in morning hours",
            category="preference",
            importance=0.8
        )
        
        # Query memory
        results = jarvis.query_memory("Android phone", top_k=3)
        print(f"Found {len(results)} relevant memories")
        
        # Get context for a topic
        context = jarvis.get_context_for_topic("morning routine", max_tokens=500)
        print(f"Context window: {context[:200]}...")
        
        # Check system status
        status = jarvis.get_system_status()
        print(f"System efficiency: {status['event_bus']['filter_efficiency_percent']}%")
        
        # Keep running
        print("\nJarvis Core running... (Ctrl+C to stop)")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        jarvis.stop()
