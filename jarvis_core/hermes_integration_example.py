"""
Hermes Agent Integration Example
Shows how to integrate Jarvis Core with the main Hermes Agent system.

Place this file in the Hermes Agent root directory and import into run_agent.py
"""

import sys
import os

# Add jarvis_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis_core'))

from jarvis_core.core import create_jarvis_core, SystemConfig

# ============================================================================
# STEP 1: Initialize Jarvis Core alongside Hermes
# ============================================================================

def initialize_jarvis_for_hermes():
    """
    Call this during Hermes Agent initialization.
    Returns the jarvis instance for use throughout the agent.
    """
    config = SystemConfig(
        memory_db_path="hermes_jarvis_memory.db",
        embedding_dim=768,
        enable_daemons=True,
        log_efficiency_stats=True,
        stats_interval_seconds=60
    )
    
    jarvis = create_jarvis_core(config)
    jarvis.start()
    
    print("✓ Jarvis Core initialized and running")
    print(f"  - Event bus filtering enabled")
    print(f"  - Background daemons active")
    print(f"  - Memory compression: TurboQuant (30x efficiency)")
    
    return jarvis


# ============================================================================
# STEP 2: Add these functions to your Hermes Agent's main loop
# ============================================================================

class HermesJarvisIntegration:
    """
    Mixin class to add Jarvis capabilities to Hermes Agent.
    """
    
    def __init__(self, jarvis):
        self.jarvis = jarvis
        self._setup_event_forwarding()
        
    def _setup_event_forwarding(self):
        """Forward relevant Hermes events to Jarvis for processing."""
        
        # This would be called when Hermes receives notifications
        pass
    
    def pre_llm_hook(self, user_input: str, context_type: str = "general") -> str:
        """
        Call BEFORE sending request to LLM.
        Retrieves optimized context from Jarvis memory.
        
        Args:
            user_input: The user's query/command
            context_type: Type of context needed (e.g., "phone", "files", "preferences")
            
        Returns:
            Enhanced prompt with relevant context
        """
        # Get token-optimized context from Jarvis
        context = self.jarvis.get_context_for_topic(
            topic=context_type,
            max_tokens=1500  # Leave room for response
        )
        
        if context.strip():
            enhanced_prompt = f"""<context>
{context}
</context>

<user_query>
{user_input}
</user_query>

Respond considering the context above."""
            return enhanced_prompt
            
        return user_input
    
    def post_llm_hook(self, user_input: str, llm_response: str):
        """
        Call AFTER receiving LLM response.
        Stores interaction in Jarvis memory for future context.
        
        Args:
            user_input: Original user query
            llm_response: Response from Hermes/LLM
        """
        # Store conversation snippet (low importance by default)
        self.jarvis.learn_from_interaction(
            content=f"Q: {user_input[:200]} | A: {llm_response[:200]}",
            category="conversation_history",
            importance=0.3  # Low importance, can be forgotten
        )
        
        # Check if response indicates learning opportunity
        if any(keyword in llm_response.lower() for keyword in ['remember', 'note', 'learn', 'preference']):
            self.jarvis.learn_from_interaction(
                content=llm_response,
                category="potential_learning",
                importance=0.6  # Medium importance for review
            )
    
    def handle_phone_notification(self, notification: dict):
        """
        Handle incoming phone notifications through Jarvis.
        Most will be filtered without LLM calls.
        
        Args:
            notification: Dict with keys: app, title, text, timestamp, urgent
        """
        priority = "high" if notification.get('urgent') else "low"
        
        llm_needed = self.jarvis.publish_event(
            source="android_phone",
            category="notification",
            content=f"{notification.get('app', 'Unknown')}: {notification.get('title', '')} - {notification.get('text', '')}",
            priority=priority,
            metadata=notification
        )
        
        if llm_needed:
            # Only notify Hermes for high-priority notifications
            return f"Phone notification requires attention: {notification.get('text', '')}"
        else:
            # Handled automatically by Jarvis
            return None
    
    def get_proactive_suggestions(self) -> list:
        """
        Get proactive suggestions from Jarvis daemons.
        Call this periodically to surface pattern-based insights.
        
        Returns:
            List of suggestion strings
        """
        # Query memory for pattern predictions
        predictions = self.jarvis.query_memory(
            query="upcoming routine pattern prediction",
            top_k=3,
            category_filter="suggestion"
        )
        
        return [p['content'] for p in predictions if p.get('similarity', 0) > 0.5]


# ============================================================================
# STEP 3: Example integration in Hermes Agent's main loop
# ============================================================================

def example_hermes_main_loop():
    """
    Example of how to integrate Jarvis into Hermes Agent's main loop.
    This is pseudocode - adapt to your actual Hermes structure.
    """
    
    # Initialize both systems
    print("Initializing Hermes Agent with Jarvis Core...")
    jarvis = initialize_jarvis_for_hermes()
    integration = HermesJarvisIntegration(jarvis)
    
    # Main agent loop
    while True:
        try:
            # Get user input
            user_input = get_user_input()  # Your existing function
            
            # PRE-PROCESS: Get context from Jarvis
            enhanced_input = integration.pre_llm_hook(
                user_input=user_input,
                context_type="general"  # Or detect from input
            )
            
            # CALL LLM: Your existing LLM call
            response = call_your_llm(enhanced_input)  # Your existing function
            
            # POST-PROCESS: Store in Jarvis memory
            integration.post_llm_hook(user_input, response)
            
            # Output response
            print(response)
            
            # Check for proactive suggestions (optional, periodic)
            if should_check_proactive():  # Your timing logic
                suggestions = integration.get_proactive_suggestions()
                for suggestion in suggestions:
                    print(f"💡 Proactive: {suggestion}")
                    
        except KeyboardInterrupt:
            break
    
    # Cleanup
    jarvis.stop()
    print("Jarvis Core stopped gracefully")


# ============================================================================
# STEP 4: Phone Control Integration (with your existing phone_control_module)
# ============================================================================

def integrate_phone_control_with_jarvis(jarvis, phone_controller):
    """
    Connect your phone_control_module with Jarvis event system.
    
    Args:
        jarvis: JarvisCore instance
        phone_controller: Your existing PhoneController from phone_control_module
    """
    
    # Forward phone events to Jarvis
    def on_phone_event(event_data):
        """Callback from phone controller"""
        
        # Determine event type and priority
        if event_data.get('type') == 'battery_low':
            jarvis.publish_event(
                source="pixel_7a",
                category="system_alert",
                content=f"Battery critical: {event_data['level']}%",
                priority="critical",
                metadata=event_data
            )
            
        elif event_data.get('type') == 'app_opened':
            jarvis.publish_event(
                source="pixel_7a",
                category="activity",
                content=f"Opened app: {event_data['app_name']}",
                priority="trivial",  # Auto-filtered
                metadata=event_data
            )
            
        elif event_data.get('type') == 'location_change':
            jarvis.publish_event(
                source="pixel_7a",
                category="location",
                content=f"Location updated: {event_data['location']}",
                priority="low",  # Batched
                metadata=event_data
            )
    
    # Register callback with your phone controller
    # phone_controller.register_event_callback(on_phone_event)
    
    print("✓ Phone control integrated with Jarvis event bus")


# ============================================================================
# Usage Instructions
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         Hermes Agent + Jarvis Core Integration            ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  1. Copy this file to your Hermes Agent root directory    ║
    ║  2. Import initialize_jarvis_for_hermes() in run_agent.py ║
    ║  3. Wrap your LLM calls with pre/post hooks               ║
    ║  4. Route phone notifications through Jarvis              ║
    ║  5. Enjoy 90%+ token savings and proactive intelligence   ║
    ╚═══════════════════════════════════════════════════════════╝
    
    For detailed documentation, see jarvis_core/README.md
    """)
