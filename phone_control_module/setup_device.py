#!/usr/bin/env python3
"""
Device Setup Script for Phone Control Module

Helps set up ADB connection with your Pixel 7a.
Run this script to configure wireless ADB.
"""

import subprocess
import sys
import time


def run_command(cmd: str, capture: bool = True) -> tuple:
    """Run shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, 
            text=True, timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def check_adb_installed() -> bool:
    """Check if ADB is installed."""
    success, _ = run_command("adb version")
    return success


def list_devices() -> list:
    """List connected ADB devices."""
    success, output = run_command("adb devices")
    if not success:
        return []
    
    devices = []
    for line in output.strip().split("\n")[1:]:
        if "\t" in line:
            parts = line.split("\t")
            if len(parts) >= 2:
                devices.append({"id": parts[0], "status": parts[1]})
    return devices


def enable_wireless_adb():
    """Enable wireless ADB on connected USB device."""
    print("\n📱 Enabling wireless ADB...")
    
    # Enable TCP/IP mode
    success, output = run_command("adb tcpip 5555")
    if not success:
        print(f"❌ Failed to enable TCP/IP: {output}")
        return False
    
    print("✅ TCP/IP mode enabled")
    time.sleep(2)
    
    # Get device IP
    success, ip_output = run_command(
        "adb shell ip -f inet addr show wlan0 | grep 'inet '"
    )
    
    if success and "inet " in ip_output:
        # Parse IP from output
        for part in ip_output.split():
            if part.startswith("192.168.") or part.startswith("10."):
                device_ip = part.split("/")[0]
                break
        else:
            print("⚠️ Could not auto-detect IP, please enter manually")
            device_ip = input("Enter your phone's WiFi IP: ").strip()
    else:
        print("⚠️ Could not auto-detect IP, please enter manually")
        device_ip = input("Enter your phone's WiFi IP: ").strip()
    
    print(f"\n📡 Device IP: {device_ip}")
    
    # Disconnect USB and connect via WiFi
    print("\n💡 You can now disconnect USB cable")
    time.sleep(1)
    
    print(f"\n🔄 Connecting to {device_ip}:5555...")
    success, output = run_command(f"adb connect {device_ip}:5555")
    
    if success and "connected" in output.lower():
        print(f"✅ Successfully connected to {device_ip}:5555")
        
        # Verify connection
        devices = list_devices()
        for dev in devices:
            if device_ip in dev["id"]:
                print(f"   Device: {dev['id']} ({dev['status']})")
                return True
    
    print(f"❌ Connection failed: {output}")
    return False


def test_connection():
    """Test the ADB connection."""
    print("\n🧪 Testing connection...")
    
    # Get device info
    success, output = run_command("adb shell getprop ro.product.model")
    if success:
        print(f"✅ Device model: {output.strip()}")
    
    success, output = run_command("adb shell wm size")
    if success:
        print(f"✅ Screen size: {output.strip()}")
    
    # Test screenshot
    print("\n📸 Testing screenshot...")
    success, _ = run_command("adb shell screencap -p /data/local/tmp/test.png")
    if success:
        print("✅ Screenshot test passed")
    
    # Test UI dump
    print("\n🔍 Testing UI element detection...")
    success, _ = run_command("adb shell uiautomator dump /data/local/tmp/ui.xml")
    if success:
        print("✅ UI element test passed")
    
    return True


def main():
    print("=" * 60)
    print("📱 Phone Control Module - Device Setup")
    print("=" * 60)
    
    # Check ADB
    if not check_adb_installed():
        print("\n❌ ADB is not installed!")
        print("\nInstall Android Platform Tools:")
        print("  - Ubuntu/Debian: sudo apt install android-tools-adb")
        print("  - macOS: brew install android-platform-tools")
        print("  - Windows: Download from developer.android.com")
        sys.exit(1)
    
    print("✅ ADB is installed")
    
    # List current devices
    devices = list_devices()
    if not devices:
        print("\n❌ No devices connected via USB")
        print("\nSteps to connect:")
        print("1. Enable Developer Options on your Pixel 7a:")
        print("   Settings → About phone → Tap 'Build number' 7 times")
        print("2. Enable USB Debugging:")
        print("   Settings → System → Developer options → USB debugging")
        print("3. Connect phone via USB")
        print("4. Accept RSA key prompt on your phone")
        print("5. Run this script again")
        sys.exit(1)
    
    print(f"\n📲 Found {len(devices)} device(s):")
    for dev in devices:
        status_icon = "✅" if dev["status"] == "device" else "⚠️"
        print(f"   {status_icon} {dev['id']} ({dev['status']})")
    
    # Check if any device is already wireless
    wireless_devices = [d for d in devices if ":" in d["id"]]
    if wireless_devices:
        print("\n✅ Wireless ADB already configured!")
        print(f"   Connected to: {wireless_devices[0]['id']}")
        
        if input("\nTest connection? (y/n): ").lower() == 'y':
            test_connection()
        return
    
    # Enable wireless ADB
    print("\n" + "=" * 60)
    print("Setting up wireless ADB...")
    print("=" * 60)
    
    if input("\nProceed with wireless setup? (y/n): ").lower() != 'y':
        print("Setup cancelled")
        return
    
    if enable_wireless_adb():
        print("\n" + "=" * 60)
        print("🎉 Wireless ADB setup complete!")
        print("=" * 60)
        
        if input("\nRun connection tests? (y/n): ").lower() == 'y':
            test_connection()
        
        print("\n📝 Next steps:")
        print("1. Use the phone_control module in Hermes Agent")
        print("2. Your device IP will be saved for future connections")
        print("3. Wireless debugging will persist across reboots")
    else:
        print("\n❌ Setup failed. Please check:")
        print("   - USB cable is connected properly")
        print("   - USB debugging is enabled")
        print("   - You accepted the RSA key prompt")
        sys.exit(1)


if __name__ == "__main__":
    main()
