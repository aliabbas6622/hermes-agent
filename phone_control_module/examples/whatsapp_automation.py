#!/usr/bin/env python3
"""
Example: Automated WhatsApp Messaging

Demonstrates sending a WhatsApp message using phone control.
"""

import sys
sys.path.insert(0, '/workspace/phone_control_module/src')

from controller import PhoneController
import time


def send_whatsapp_message(phone: PhoneController, contact: str, message: str):
    """Send a WhatsApp message to a contact."""
    
    print("\n📱 Launching WhatsApp...")
    phone.launch_app("com.whatsapp")
    time.sleep(2)
    
    # Wait for app to load - check if we're on main screen
    print("🔍 Looking for chat interface...")
    elements = phone.get_screen_elements()
    
    # Try to find "New chat" or similar button
    new_chat_elem = phone.find_element(text_contains="new")
    if new_chat_elem:
        print("   Found 'New chat' option")
        phone.input.tap_element(new_chat_elem)
        time.sleep(1)
    
    # Search for contact
    print(f"🔍 Searching for contact: {contact}")
    phone.type_text(contact)
    time.sleep(2)
    
    # Tap on contact name
    contact_elem = phone.find_element(text_contains=contact)
    if contact_elem:
        print(f"   Found contact: {contact}")
        phone.input.tap_element(contact_elem)
        time.sleep(1)
    else:
        print("   ⚠️ Contact not found, trying alternative...")
        # Try tapping first search result
        phone.input.tap(540, 400)
        time.sleep(1)
    
    # Type message
    print(f"✏️ Typing message...")
    phone.type_text(message)
    time.sleep(1)
    
    # Find and tap send button (green send button)
    print("📤 Sending message...")
    send_elem = phone.find_element(text_contains="send")
    if send_elem:
        phone.input.tap_element(send_elem)
    else:
        # Tap approximate location of send button (bottom right)
        width, height = phone.screen.get_screen_size()
        phone.tap(int(width * 0.9), int(height * 0.9))
    
    time.sleep(1)
    print("✅ Message sent!")
    
    # Return to home
    phone.press_home()


def main():
    print("=" * 60)
    print("💬 WhatsApp Automation Example")
    print("=" * 60)
    
    DEVICE_IP = "192.168.1.100"  # Change to your device IP
    
    print(f"\nConnecting to {DEVICE_IP}...")
    phone = PhoneController(device_ip=DEVICE_IP)
    
    if not phone.is_connected():
        print("❌ Connection failed!")
        return
    
    print("✅ Connected!")
    
    # Get device info
    info = phone.get_device_info()
    print(f"\n📋 Device: {info.get('model', 'Unknown')} ({info.get('android_version', '?')})")
    
    # Example usage
    print("\n" + "=" * 60)
    print("This example shows how to automate WhatsApp messaging.")
    print("Modify the contact and message below to test.")
    print("=" * 60)
    
    # Uncomment to actually send a message:
    # send_whatsapp_message(
    #     phone, 
    #     contact="John Doe", 
    #     message="Hello from Hermes Agent! 🤖"
    # )
    
    print("\n📝 To send a message, edit this script and:")
    print("   1. Set your device IP")
    print("   2. Uncomment the send_whatsapp_message() call")
    print("   3. Set your contact name and message")
    print("   4. Run the script")
    
    print("\n⚠️ Note:")
    print("   - Keep your phone unlocked during automation")
    print("   - WhatsApp must be installed")
    print("   - First run may require manual interaction")
    
    phone.disconnect()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
