#!/usr/bin/env python3
"""
Advanced Cloudflare bypass script for GMGN.ai
Uses multiple techniques to bypass Cloudflare protection
"""

import time
import random
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService

def create_stealth_firefox():
    """Create a highly stealth Firefox instance"""
    options = FirefoxOptions()
    
    # Maximum stealth arguments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu-logging")
    options.add_argument("--silent")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu-logging")
    options.add_argument("--silent")
    options.add_argument("--log-level=3")
    
    # Random user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    ]
    selected_ua = random.choice(user_agents)
    options.set_preference("general.useragent.override", selected_ua)
    
    # Advanced stealth preferences
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("marionette.enabled", True)
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("media.volume_scale", "0.0")
    options.set_preference("dom.push.enabled", False)
    options.set_preference("geo.enabled", False)
    options.set_preference("browser.search.suggest.enabled", False)
    options.set_preference("browser.urlbar.suggest.searches", False)
    options.set_preference("privacy.trackingprotection.enabled", False)
    options.set_preference("browser.safebrowsing.enabled", False)
    options.set_preference("browser.safebrowsing.malware.enabled", False)
    options.set_preference("browser.safebrowsing.phishing.enabled", False)
    options.set_preference("dom.event.clipboard.enabled", False)
    options.set_preference("media.navigator.enabled", False)
    options.set_preference("media.peerconnection.enabled", False)
    options.set_preference("webgl.disabled", True)
    options.set_preference("canvas.poisondata", True)
    options.set_preference("canvas.image.cache", False)
    
    return options

def bypass_cloudflare(driver, url, max_attempts=3):
    """Attempt to bypass Cloudflare protection"""
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts} to bypass Cloudflare...")
            
            # Random delay
            time.sleep(random.uniform(3, 8))
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page load
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check for Cloudflare challenge
            time.sleep(random.uniform(5, 10))
            
            # Look for Cloudflare indicators
            cloudflare_indicators = [
                "Checking your browser",
                "Please wait",
                "DDoS protection",
                "Just a moment",
                "Verifying you are human"
            ]
            
            page_text = driver.page_source.lower()
            is_cloudflare = any(indicator.lower() in page_text for indicator in cloudflare_indicators)
            
            if is_cloudflare:
                print("Cloudflare challenge detected, waiting...")
                time.sleep(random.uniform(15, 30))
                
                # Try to click through challenge if possible
                try:
                    # Look for "Continue" or "Proceed" buttons
                    continue_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Proceed') or contains(text(), 'Verify')]")
                    if continue_buttons:
                        continue_buttons[0].click()
                        time.sleep(random.uniform(3, 7))
                except:
                    pass
                
                # Check if challenge is resolved
                time.sleep(random.uniform(5, 10))
                page_text_after = driver.page_source.lower()
                is_cloudflare_after = any(indicator.lower() in page_text_after for indicator in cloudflare_indicators)
                
                if not is_cloudflare_after:
                    print("✅ Cloudflare challenge bypassed!")
                    return True
                else:
                    print("❌ Cloudflare challenge still present")
                    if attempt < max_attempts - 1:
                        print("Retrying...")
                        time.sleep(random.uniform(10, 20))
            else:
                print("✅ No Cloudflare challenge detected")
                return True
                
        except Exception as e:
            print(f"Error in attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(5, 10))
    
    return False

def main():
    """Main function to test Cloudflare bypass"""
    print("🛡️ Cloudflare Bypass Test")
    print("=" * 50)
    
    # Create stealth Firefox
    options = create_stealth_firefox()
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        # Execute stealth JavaScript
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', filename: 'internal-nacl-plugin'}
        ]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        if (!window.chrome) window.chrome = {};
        if (!window.chrome.runtime) window.chrome.runtime = {};
        """
        driver.execute_script(stealth_script)
        
        # Test URLs
        test_urls = [
            "https://gmgn.ai",
            "https://gmgn.ai/sol/address/4eK5n4LUoCHbxyrem1erKHPAbzajv76g2jNxopTYRKVf"
        ]
        
        for url in test_urls:
            print(f"\n🌐 Testing: {url}")
            success = bypass_cloudflare(driver, url)
            
            if success:
                print(f"✅ Successfully accessed: {url}")
                print(f"Page length: {len(driver.page_source)} characters")
                
                # Check for specific content
                if "gmgn" in driver.page_source.lower():
                    print("✅ GMGN content detected")
                else:
                    print("⚠️  GMGN content not found")
            else:
                print(f"❌ Failed to bypass Cloudflare for: {url}")
        
        print("\n💡 If Cloudflare is still blocking:")
        print("1. Try using a VPN")
        print("2. Use manual browser mode")
        print("3. Try different times of day")
        print("4. Use residential proxies")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
