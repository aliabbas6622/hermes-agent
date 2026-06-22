"""
PROJECT NEXUS: Proactive Prediction Engine
"""
import asyncio
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.proactive")

class PatternType(Enum):
    TEMPORAL = "temporal"
    SEQUENTIAL = "sequential"

@dataclass
class BehavioralPattern:
    id: str
    pattern_type: PatternType
    description: str
    trigger_conditions: Dict[str, Any]
    expected_actions: List[str]
    confidence: float = 0.0
    occurrences: int = 0

@dataclass
class AnomalyAlert:
    id: str
    anomaly_type: str
    description: str
    severity: str
    detected_at: float
    metrics: Dict[str, Any]
    baseline: Dict[str, Any]

class TimeSeriesBuffer:
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
    
    def add(self, value: float):
        self.buffer.append(value)
    
    def get_stats(self) -> Dict[str, float]:
        if not self.buffer:
            return {}
        data = list(self.buffer)
        return {
            "mean": statistics.mean(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "latest": data[-1]
        }
    
    def detect_spike(self, threshold: float = 3.0) -> bool:
        if len(self.buffer) < 10:
            return False
        stats = self.get_stats()
        if stats["stdev"] == 0:
            return False
        z_score = abs(stats["latest"] - stats["mean"]) / stats["stdev"]
        return z_score > threshold

class ProactivePredictor:
    def __init__(self):
        self.patterns: Dict[str, BehavioralPattern] = {}
        self.anomaly_detectors: Dict[str, TimeSeriesBuffer] = {}
        self.action_history = deque(maxlen=1000)
        self._running = False
    
    def update_metric(self, metric_name: str, value: float):
        if metric_name not in self.anomaly_detectors:
            self.anomaly_detectors[metric_name] = TimeSeriesBuffer()
        self.anomaly_detectors[metric_name].add(value)
    
    def record_action(self, action: str, context: Dict = None):
        self.action_history.append({"action": action, "timestamp": time.time(), "context": context or {}})
    
    async def get_proactive_suggestions(self) -> List[Dict]:
        suggestions = []
        for name, detector in self.anomaly_detectors.items():
            if detector.detect_spike(2.0):
                suggestions.append({
                    "type": "alert",
                    "title": f"{name.replace('_', ' ').title()} Anomaly",
                    "message": f"Unusual {name} detected",
                    "actions": ["investigate"]
                })
        return suggestions
    
    def start_monitoring(self):
        self._running = True
        logger.info("Proactive predictor started")
    
    def stop_monitoring(self):
        self._running = False

predictor = ProactivePredictor()
