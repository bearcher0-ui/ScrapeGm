#!/usr/bin/env python3
"""
Alternative approach to bypass GMGN.ai blocking.
This script provides multiple methods to access GMGN.ai data.
"""

import time
import json
from pathlib import Path

def method_1_manual_browser():
    """Method 1: Manual browser with instructions"""
    print("🌐 Method 1: Manual Browser")
    print("=" * 50)
    print("1. Open your regular browser (Chrome/Firefox)")
    print("2. Go to https://gmgn.ai")
    print("3. Login normally")
    print("4. Navigate to your wallet page")
    print("5. Right-click -> 'Save Page As' -> HTML file")
    print("6. Use the HTML file with the scraper:")
    print("   python gmgn_scrape.py --html saved_file.html --wallet 'My_Wallet' --debug")
    print("=" * 50)

def method_2_mobile_user_agent():
    """Method 2: Use mobile user agent"""
    print("📱 Method 2: Mobile User Agent")
    print("=" * 50)
    print("Mobile browsers are often less blocked:")
    print("1. Open Chrome DevTools (F12)")
    print("2. Click device toggle (phone icon)")
    print("3. Select iPhone or Android")
    print("4. Refresh the page")
    print("5. Login normally")
    print("6. Save the page as HTML")
    print("=" * 50)

def method_3_incognito_mode():
    """Method 3: Incognito/Private mode"""
    print("🕵️ Method 3: Incognito Mode")
    print("=" * 50)
    print("Incognito mode often bypasses some blocks:")
    print("1. Open Chrome Incognito (Ctrl+Shift+N)")
    print("2. Go to https://gmgn.ai")
    print("3. Login normally")
    print("4. Navigate to wallet page")
    print("5. Save as HTML")
    print("=" * 50)

def method_4_different_browser():
    """Method 4: Use different browser"""
    print("🔄 Method 4: Different Browser")
    print("=" * 50)
    print("Try different browsers:")
    print("1. Firefox (often less blocked)")
    print("2. Edge")
    print("3. Safari (if on Mac)")
    print("4. Opera")
    print("5. Brave browser")
    print("=" * 50)

def method_5_vpn_proxy():
    """Method 5: VPN/Proxy"""
    print("🌍 Method 5: VPN/Proxy")
    print("=" * 50)
    print("Change your IP address:")
    print("1. Use VPN (NordVPN, ExpressVPN, etc.)")
    print("2. Try different server locations")
    print("3. Use proxy services")
    print("4. Try mobile hotspot")
    print("=" * 50)

def method_6_api_alternative():
    """Method 6: Alternative data sources"""
    print("🔌 Method 6: Alternative Data Sources")
    print("=" * 50)
    print("Try these alternatives to GMGN.ai:")
    print("1. Solscan.io - https://solscan.io/account/YOUR_WALLET")
    print("2. SolanaFM - https://solana.fm/account/YOUR_WALLET")
    print("3. Solana Beach - https://solanabeach.io/address/YOUR_WALLET")
    print("4. Birdeye - https://birdeye.so/portfolio/YOUR_WALLET")
    print("5. DexScreener - https://dexscreener.com/solana/YOUR_WALLET")
    print("=" * 50)

def create_stealth_script():
    """Create a stealth browser script"""
    script_content = '''#!/usr/bin/env python3
"""
Stealth browser script with maximum anti-detection
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import random

def stealth_browser():
    options = Options()
    
    # Maximum stealth options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Random delays
    time.sleep(random.uniform(1, 3))
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Hide automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        print("Opening GMGN.ai...")
        driver.get("https://gmgn.ai")
        
        print("Please login manually...")
        input("Press ENTER when logged in...")
        
        # Navigate to wallet
        wallet = input("Enter wallet address: ")
        driver.get(f"https://gmgn.ai/sol/address/{wallet}")
        
        print("Save the page as HTML file")
        input("Press ENTER when done...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    stealth_browser()
'''
    
    with open("stealth_browser.py", "w") as f:
        f.write(script_content)
    
    print("📝 Created stealth_browser.py")
    print("Run: python stealth_browser.py")

def main():
    print("🚀 GMGN.ai Blocking Bypass Methods")
    print("=" * 60)
    
    methods = [
        method_1_manual_browser,
        method_2_mobile_user_agent,
        method_3_incognito_mode,
        method_4_different_browser,
        method_5_vpn_proxy,
        method_6_api_alternative
    ]
    
    for i, method in enumerate(methods, 1):
        method()
        print()
    
    create_stealth_script()
    
    print("💡 Additional Tips:")
    print("- Clear browser cookies and cache")
    print("- Try different times of day")
    print("- Use residential proxies")
    print("- Try browser automation tools like Playwright")
    print("- Consider using GMGN.ai mobile app")

if __name__ == "__main__":
    main()
