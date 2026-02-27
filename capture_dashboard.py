# capture_dashboard.py
# This saves your dashboard as HTML and PNG

import subprocess
import time
import os

print("📸 Dashboard Capture Tool")
print("=" * 40)
print("Make sure your Streamlit app is running!")
print("=" * 40)

# Method 1 - Save screenshots using PIL
try:
    import pyautogui
    pip_install = subprocess.run(
        ["pip", "install", "pyautogui", "pillow"],
        capture_output=True
    )

    print("\n📸 Taking screenshot in 5 seconds...")
    print("Switch to your browser now!")
    time.sleep(5)

    screenshot = pyautogui.screenshot()
    screenshot.save("dashboard_screenshot.png")
    print("✅ Screenshot saved as dashboard_screenshot.png")

except Exception as e:
    print(f"Note: {e}")
    print("Use Windows + Shift + S instead")