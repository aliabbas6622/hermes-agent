#!/usr/bin/env python3
"""
Example: Basic Phone Control

Demonstrates basic phone control operations with Hermes Agent.
"""

import sys
sys.path.insert(0, '/workspace/phone_control_module/src')

from controller import PhoneController


def main():
    print("=" * 60)
    print("📱 Phone Control Example")
    print("=" * 60)
    
    # Initialize controller (replace with your device IP)
    DEVICE_IP = "192.168.1.100"  # Change to your Pixel 7a's IP
    
    print(f"\nConnecting to {DEVICE_IP}...")
    phone = PhoneController(device_ip=DEVICE_IP, auto_connect=True)
    
    if not phone.is_connected():
        print("❌ Failed to connect!")
        print("\nMake sure:")
        print("  1. Wireless debugging is enabled on your Pixel 7a")
        print("  2. Your phone and computer are on the same WiFi network")
        print("  3. You've run setup_device.py first")
        return
    
    print("✅ Connected successfully!")
    
    # Get device info
    print("\n📋 Device Information:")
    info = phone.get_device_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Take a screenshot
    print("\n📸 Taking screenshot...")
    img = phone.screenshot(save_path="/tmp/phone_screen.png")
    print(f"   Resolution: {img.size}")
    print("   Saved to: /tmp/phone_screen.png")
    
    # Get UI elements
    print("\n🔍 Getting UI elements...")
    elements = phone.get_screen_elements()
    print(f"   Found {len(elements)} elements")
    
    if elements:
        print("\n   First 5 elements:")
        for i, elem in enumerate(elements[:5]):
            text = elem.get('text', '')[:30] or '[no text]'
            print(f"   {i+1}. {text} @ ({elem['center_x']}, {elem['center_y']})")
    
    # Example: Find and tap an element
    print("\n👆 Looking for 'Settings' element...")
    settings_elem = phone.find_element(text_contains="settings")
    if settings_elem:
        print("   Found! (Not tapping in this example)")
    else:
        print("   Not found on current screen")
    
    # Show available tools
    print("\n🛠️ Available Hermes Agent Tools:")
    tools = PhoneController.get_hermes_tools()
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    print("\n" + "=" * 60)
    print("✅ Example complete!")
    print("=" * 60)
    
    # Cleanup
    phone.disconnect()


if __name__ == "__main__":
    main()
