"""
Background Intelligence Daemons
Autonomous loops that run continuously to provide proactive assistance.
Monitors patterns, predicts needs, and maintains system health.
"""

import time
import threading
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import our event bus
from jarvis_core.events.event_bus import TokenEfficientEventBus, Event, Priority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.daemons")

@dataclass
class DaemonConfig:
    name: str
    interval_seconds: float
    enabled: bool = True
    priority: int = 5  # 1=highest, 10=lowest
    config: Dict = None

class PatternRecognizer:
    """
    Detects recurring user behavior patterns without ML overhead.
    Uses simple frequency analysis and time-window clustering.
    """
    
    def __init__(self, window_hours: int = 24):
        self.window_hours = window_hours
        self.event_history: List[Dict] = []
        self.patterns: Dict[str, Dict] = {}
        
    def record(self, event_type: str, timestamp: float, metadata: Dict = None):
        """Record an event for pattern analysis."""
        self.event_history.append({
            'type': event_type,
            'time': timestamp,
            'hour': datetime.fromtimestamp(timestamp).hour,
            'metadata': metadata or {}
        })
        
        # Keep only recent history
        cutoff = time.time() - (self.window_hours * 3600)
        self.event_history = [e for e in self.event_history if e['time'] > cutoff]
        
        # Update patterns
        self._analyze_patterns()
        
    def _analyze_patterns(self):
        """Identify recurring patterns in event history."""
        # Group by event type
        by_type: Dict[str, List] = {}
        for event in self.event_history:
            t = event['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(event)
            
        # Find patterns for each type
        for event_type, events in by_type.items():
            if len(events) < 3:  # Need minimum occurrences
                continue
                
            # Analyze time clustering
            hours = [e['hour'] for e in events]
            avg_hour = sum(hours) / len(hours)
            
            # Check consistency (standard deviation approximation)
            variance = sum((h - avg_hour) ** 2 for h in hours) / len(hours)
            std_dev = variance ** 0.5
            
            if std_dev < 2.0:  # Consistent timing (within ~2 hours)
                self.patterns[event_type] = {
                    'avg_hour': avg_hour,
                    'frequency': len(events) / self.window_hours,
                    'consistency': 1.0 - (std_dev / 12.0),  # Normalize to 0-1
                    'last_seen': max(e['time'] for e in events),
                    'predictable': True
                }
            else:
                self.patterns[event_type] = {
                    'predictable': False,
                    'frequency': len(events) / self.window_hours
                }
    
    def get_predictions(self, lookahead_hours: int = 2) -> List[Dict]:
        """Predict likely upcoming events based on patterns."""
        current_hour = datetime.now().hour
        predictions = []
        
        for event_type, pattern in self.patterns.items():
            if not pattern.get('predictable', False):
                continue
                
            avg_hour = pattern['avg_hour']
            # Calculate hours until next expected occurrence
            hours_until = (avg_hour - current_hour) % 24
            
            if hours_until <= lookahead_hours:
                predictions.append({
                    'event_type': event_type,
                    'expected_in_hours': hours_until,
                    'confidence': pattern['consistency'],
                    'suggestion': f"Likely to {event_type} in {hours_until:.1f} hours"
                })
                
        return sorted(predictions, key=lambda x: x['expected_in_hours'])

class BaseDaemon:
    """Base class for all background daemons."""
    
    def __init__(self, config: DaemonConfig, event_bus: TokenEfficientEventBus):
        self.config = config
        self.event_bus = event_bus
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start daemon in background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Daemon '{self.config.name}' started")
        
    def stop(self):
        """Stop daemon gracefully."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Daemon '{self.config.name}' stopped")
        
    def _run_loop(self):
        """Main daemon loop."""
        while self.running:
            try:
                self.execute()
            except Exception as e:
                logger.error(f"Daemon '{self.config.name}' error: {e}")
                
            # Sleep with early wake capability
            for _ in range(int(self.config.interval_seconds * 10)):
                if not self.running:
                    break
                time.sleep(0.1)
                
    def execute(self):
        """Override this method in subclasses."""
        raise NotImplementedError

class HealthMonitorDaemon(BaseDaemon):
    """
    Monitors system health across all connected devices.
    Publishes alerts for battery, storage, connectivity issues.
    """
    
    def execute(self):
        # Simulated health checks (integrate with actual device APIs)
        checks = [
            {'type': 'battery', 'threshold': 20, 'current': self._check_battery()},
            {'type': 'storage', 'threshold': 90, 'current': self._check_storage()},
            {'type': 'memory', 'threshold': 85, 'current': self._check_memory()},
        ]
        
        for check in checks:
            if check['current'] is None:
                continue
                
            if check['type'] == 'battery' and check['current'] < check['threshold']:
                self.event_bus.publish(Event(
                    source="health_monitor",
                    category="system_alert",
                    content=f"Low battery: {check['current']}% remaining",
                    priority=Priority.HIGH,
                    metadata={'level': check['current']}
                ))
                
            elif check['type'] == 'storage' and check['current'] > check['threshold']:
                self.event_bus.publish(Event(
                    source="health_monitor",
                    category="system_alert",
                    content=f"Storage critical: {check['current']}% full",
                    priority=Priority.MEDIUM,
                    metadata={'level': check['current']}
                ))
    
    def _check_battery(self) -> Optional[int]:
        # TODO: Integrate with phone_control_module to get real battery level
        return None
        
    def _check_storage(self) -> Optional[int]:
        # TODO: Check disk usage on laptop and phone
        return None
        
    def _check_memory(self) -> Optional[int]:
        # TODO: Check RAM usage
        return None

class PatternLearningDaemon(BaseDaemon):
    """
    Continuously learns user behavior patterns.
    Generates proactive suggestions based on recognized patterns.
    """
    
    def __init__(self, config: DaemonConfig, event_bus: TokenEfficientEventBus):
        super().__init__(config, event_bus)
        self.recognizer = PatternRecognizer()
        self.last_prediction_time = 0
        
    def execute(self):
        # Record recent events (would integrate with event bus history)
        # For now, just check for pattern-based predictions
        
        now = time.time()
        if now - self.last_prediction_time > 3600:  # Every hour
            predictions = self.recognizer.get_predictions(lookahead_hours=2)
            
            for pred in predictions[:3]:  # Top 3 predictions
                if pred['confidence'] > 0.7:
                    self.event_bus.publish(Event(
                        source="pattern_learning",
                        category="suggestion",
                        content=f"Proactive: {pred['suggestion']}",
                        priority=Priority.LOW,
                        metadata=pred
                    ))
                    
            self.last_prediction_time = now
    
    def learn_from_event(self, event: Event):
        """Feed events into pattern recognizer."""
        self.recognizer.record(
            event_type=f"{event.source}:{event.category}",
            timestamp=event.timestamp,
            metadata=event.metadata
        )

class ContextPreloadDaemon(BaseDaemon):
    """
    Pre-loads relevant context before user requests.
    Reduces perceived latency by anticipating needs.
    """
    
    def __init__(self, config: DaemonConfig, event_bus: TokenEfficientEventBus,
                 memory_bridge=None):
        super().__init__(config, event_bus)
        self.memory_bridge = memory_bridge
        self.last_context_update = {}
        
    def execute(self):
        if not self.memory_bridge:
            return
            
        # Identify current context (time of day, location, active app)
        current_context = self._get_current_context()
        context_key = hash(str(current_context))
        
        # Avoid redundant pre-loading
        if context_key in self.last_context_update:
            if time.time() - self.last_context_update[context_key] < 300:
                return
        
        # Pre-fetch relevant memories
        topic = current_context.get('topic', 'general')
        self.memory_bridge.retrieve_relevant(query=topic, top_k=10)
        
        self.last_context_update[context_key] = time.time()
        logger.debug(f"Pre-loaded context for: {topic}")
    
    def _get_current_context(self) -> Dict:
        """Determine current context from system state."""
        hour = datetime.now().hour
        
        # Simple time-based context inference
        if 6 <= hour < 10:
            topic = "morning_routine"
        elif 10 <= hour < 12:
            topic = "work_tasks"
        elif 12 <= hour < 14:
            topic = "lunch_break"
        elif 14 <= hour < 18:
            topic = "afternoon_work"
        elif 18 <= hour < 22:
            topic = "evening_activities"
        else:
            topic = "night_routine"
            
        return {
            'hour': hour,
            'topic': topic,
            'day_of_week': datetime.now().weekday()
        }

class DaemonManager:
    """
    Manages lifecycle of all background daemons.
    Provides unified start/stop and configuration.
    """
    
    def __init__(self, event_bus: TokenEfficientEventBus, memory_bridge=None):
        self.event_bus = event_bus
        self.memory_bridge = memory_bridge
        self.daemons: Dict[str, BaseDaemon] = {}
        
        self._register_default_daemons()
        
    def _register_default_daemons(self):
        """Register built-in daemons."""
        
        # Health Monitor - every 5 minutes
        self.register(DaemonConfig(
            name="health_monitor",
            interval_seconds=300,
            priority=1
        ), HealthMonitorDaemon)
        
        # Pattern Learning - every minute
        self.register(DaemonConfig(
            name="pattern_learning",
            interval_seconds=60,
            priority=3
        ), PatternLearningDaemon)
        
        # Context Preload - every 2 minutes
        self.register(DaemonConfig(
            name="context_preload",
            interval_seconds=120,
            priority=5,
            config={'topic': 'general'}
        ), ContextPreloadDaemon)
        
    def register(self, config: DaemonConfig, daemon_class: type):
        """Register a custom daemon."""
        if config.name in self.daemons:
            logger.warning(f"Daemon '{config.name}' already registered, replacing")
            
        daemon = daemon_class(config, self.event_bus)
        
        # Special handling for daemons needing memory bridge
        if config.name == "context_preload" and self.memory_bridge:
            daemon.memory_bridge = self.memory_bridge
            
        self.daemons[config.name] = daemon
        
    def start_all(self):
        """Start all enabled daemons."""
        for name, daemon in self.daemons.items():
            if daemon.config.enabled:
                daemon.start()
                
    def stop_all(self):
        """Stop all daemons gracefully."""
        for name, daemon in self.daemons.items():
            daemon.stop()
            
    def get_status(self) -> Dict:
        """Return status of all daemons."""
        return {
            name: {
                'running': daemon.running,
                'interval': daemon.config.interval_seconds,
                'enabled': daemon.config.enabled
            }
            for name, daemon in self.daemons.items()
        }
