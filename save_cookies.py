#!/usr/bin/env python3
"""
Helper script to save GMGN.ai cookies for authentication.
Run this after manually logging into GMGN.ai to save cookies for future use.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def save_gmgn_cookies(cookies_file: str = "gmgn_cookies.json"):
    """Save GMGN.ai cookies after manual login"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Initialize Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("🌐 Opening GMGN.ai...")
        driver.get("https://gmgn.ai")
        
        print("\n🔐 Please login to GMGN.ai in the browser window:")
        print("1. Click 'Login' or 'Connect Wallet' button")
        print("2. Complete the login process")
        print("3. Navigate to any wallet page to verify login")
        print("4. Press ENTER here when done...")
        
        input("Press ENTER when login is complete...")
        
        # Verify login
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        if "/address/" in current_url or "dashboard" in current_url.lower():
            print("✅ Login verified!")
        else:
            print("⚠️  Warning: Login verification unclear")
        
        # Save cookies
        cookies = driver.get_cookies()
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f)
        
        print(f"✅ Cookies saved to {cookies_file}")
        print(f"💡 Use these cookies with: --cookies {cookies_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    cookies_file = sys.argv[1] if len(sys.argv) > 1 else "gmgn_cookies.json"
    save_gmgn_cookies(cookies_file)
