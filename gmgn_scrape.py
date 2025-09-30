import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup  # type: ignore
import pandas as pd  # type: ignore
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


MONEY_REGEX = re.compile(r"-?\$\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\$\s?\d+(?:\.\d+)?")


def read_file_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()




def normalize_money_to_float(text: str) -> Optional[float]:
    m = MONEY_REGEX.search(text)
    if not m:
        return None
    amt = m.group(0)
    # Remove currency symbols and spaces, keep sign
    amt = amt.replace("$", "").replace(",", "").strip()
    try:
        return float(amt)
    except ValueError:
        return None


def extract_7d_realized_pnl_from_html(html: str, debug: bool = False) -> Tuple[Optional[float], Dict[str, Any]]:
    info: Dict[str, Any] = {"strategy": None, "context": None}

    # Heuristic 0: Targeted CSS selector for GMGN's 7D Realized PnL div
    soup = BeautifulSoup(html, "lxml")
    # Look for divs with the specific GMGN styling that contain money values
    target_divs = soup.find_all("div", class_=re.compile(r"flex.*font-medium.*text-\[12px\].*ml-\[4px\]"))
    for div in target_divs:
        text = div.get_text(strip=True)
        if MONEY_REGEX.search(text):
            # Check if this div is in context of 7D/Realized/PnL
            parent_context = ""
            for parent in div.parents:
                if parent.get_text:
                    parent_text = parent.get_text(strip=True)
                    if re.search(r"7\s*D|Realized|PnL|Profit", parent_text, re.IGNORECASE):
                        parent_context = parent_text[:200]
                        break
            if parent_context or re.search(r"7\s*D|Realized|PnL|Profit", text, re.IGNORECASE):
                money_match = MONEY_REGEX.search(text)
                if money_match:
                    info["strategy"] = "targeted_css_selector"
                    info["context"] = f"Div: {text}, Parent: {parent_context[:100]}"
                    if debug:
                        info["raw_money"] = money_match.group(0)
                    return normalize_money_to_float(money_match.group(0)), info

    # Also try broader search for any div with the red color style (decrease-100)
    red_divs = soup.find_all("div", style=re.compile(r"color:\s*rgb\(242,\s*102,\s*130\)"))
    for div in red_divs:
        text = div.get_text(strip=True)
        if MONEY_REGEX.search(text):
            # Check context for 7D/Realized
            parent_text = ""
            for parent in div.parents:
                if parent.get_text:
                    parent_text = parent.get_text(strip=True)
                    if re.search(r"7\s*D|Realized|PnL|Profit", parent_text, re.IGNORECASE):
                        break
            if re.search(r"7\s*D|Realized|PnL|Profit", parent_text, re.IGNORECASE):
                money_match = MONEY_REGEX.search(text)
                if money_match:
                    info["strategy"] = "red_color_style_selector"
                    info["context"] = f"Red div: {text}, Context: {parent_text[:100]}"
                    if debug:
                        info["raw_money"] = money_match.group(0)
                    return normalize_money_to_float(money_match.group(0)), info

    # Heuristic 1: Find an "Analysis" card and within it a block mentioning 7D + (Realized|Profit|PnL)

    # Locate the Analysis card container
    analysis_card = None
    for el in soup.find_all(string=True):
        t = (el.string or "").strip()
        if t == "Analysis":
            # Prefer the parent that looks like a card (has padding classes or rounded)
            parent = el
            for _ in range(5):
                if not parent or not getattr(parent, "parent", None):
                    break
                parent = parent.parent
                if not getattr(parent, "get", None):
                    continue
                cls = parent.get("class") or []
                # Tailwind-like classes appear in the saved HTML
                if any(c.startswith("bg-") or c.startswith("p-") or c.startswith("rounded-") for c in cls):
                    analysis_card = parent
                    break
            if analysis_card is not None:
                break

    def find_money_near_keywords(container) -> Optional[str]:
        if not container:
            return None
        # Gather text blocks and look for segments with 7D and realized/pnl/profit
        texts = []
        for t in container.stripped_strings:
            if t:
                texts.append(t)
        joined = " \n ".join(texts)
        # First try tight keyword combo
        patterns = [
            r"7\s*D[^\n]*?(Realized|Profit|PnL)[^\n]*?\$\s?-?\d[\d,]*(?:\.\d+)?",
            r"(Realized|Profit|PnL)[^\n]*?7\s*D[^\n]*?\$\s?-?\d[\d,]*(?:\.\d+)?",
        ]
        for pat in patterns:
            m = re.search(pat, joined, re.IGNORECASE)
            if m:
                money = MONEY_REGEX.search(m.group(0))
                if money:
                    return money.group(0)
        # Fallback: find a line with 7D and then the first money amount in next ~300 chars
        m7 = re.search(r"7\s*D", joined, re.IGNORECASE)
        if m7:
            seg = joined[m7.start() : m7.start() + 300]
            money = MONEY_REGEX.search(seg)
            if money:
                return money.group(0)
        # Last resort: any money in the card (often first is 7D)
        money_any = MONEY_REGEX.search(joined)
        return money_any.group(0) if money_any else None

    # Try inside Analysis card first
    money_txt: Optional[str] = None
    if analysis_card is not None:
        money_txt = find_money_near_keywords(analysis_card)
        if money_txt:
            info["strategy"] = "analysis_card_keywords"
            info["context"] = "Analysis card"

    # Heuristic 2: Global search in HTML text around occurrences of '7D' and 'Realized'
    if not money_txt:
        raw = html
        # Prefer vicinity window around '7D' then 'Realized/Profit/PnL'
        for m in re.finditer(r"7\s*D", raw, flags=re.IGNORECASE):
            window = raw[max(0, m.start() - 200) : m.end() + 400]
            m_money = MONEY_REGEX.search(window)
            if m_money:
                money_txt = m_money.group(0)
                info["strategy"] = "raw_text_vicinity_7d"
                info["context"] = window[:200]
                break

    # Heuristic 3: Any explicit label for Realized Profit/PnL with money
    if not money_txt:
        for pat in [r"Realized\s*(Profit|PnL)[^\n]*\$\s?-?\d", r"\bPnL\b[^\n]*\$\s?-?\d"]:
            m = re.search(pat, html, flags=re.IGNORECASE)
            if m:
                m_money = MONEY_REGEX.search(m.group(0))
                if m_money:
                    money_txt = m_money.group(0)
                    info["strategy"] = "label_global"
                    info["context"] = m.group(0)[:120]
                    break

    # Heuristic 4: Parse embedded JSON (Next.js data or inline state) for realized 7d fields
    if not money_txt:
        json_money = _extract_money_from_embedded_json(html)
        if json_money:
            money_txt = json_money
            info["strategy"] = "embedded_json_7d"
            info["context"] = "__NEXT_DATA__ or inline JSON"

    value = normalize_money_to_float(money_txt or "") if money_txt else None
    if debug:
        info["raw_money"] = money_txt
    return value, info


def extract_from_plain_text(text: str) -> Optional[str]:
    # Look for a section mentioning 7D and realized/profit/pnl nearby, then money
    patterns = [
        r"7\s*D[^\n]*?(Realized|Profit|PnL)[^\n]*?\$\s?-?\d[\d,]*(?:\.\d+)?",
        r"(Realized|Profit|PnL)[^\n]*?7\s*D[^\n]*?\$\s?-?\d[\d,]*(?:\.\d+)?",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            mm = MONEY_REGEX.search(m.group(0))
            if mm:
                return mm.group(0)
    # Fallback: proximity search around 7D
    for m in re.finditer(r"7\s*D", text, flags=re.IGNORECASE):
        seg = text[max(0, m.start() - 200) : m.end() + 400]
        mm = MONEY_REGEX.search(seg)
        if mm:
            return mm.group(0)
    return None


def _extract_money_from_embedded_json(html: str) -> Optional[str]:
    # Grab likely JSON blobs
    soup = BeautifulSoup(html, "lxml")
    candidates = []
    # Next.js
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd and nd.string:
        candidates.append(nd.string)
    # Any application/json scripts
    for s in soup.find_all("script", attrs={"type": "application/json"}):
        if s.string:
            candidates.append(s.string)
    # Also scan inline JS text blocks roughly
    for s in soup.find_all("script"):
        if s.string and ("7d" in s.string.lower() or "realiz" in s.string.lower() or "pnl" in s.string.lower()):
            candidates.append(s.string)

    patterns_key = re.compile(r"(7\s*d|seven\s*day).*?(realiz|pnl|profit)|" r"(realiz|pnl|profit).*?(7\s*d|seven\s*day)", re.IGNORECASE | re.DOTALL)

    def search_in_obj(obj: Any) -> Optional[str]:
        try:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = str(k)
                    if re.search(patterns_key, key):
                        if isinstance(v, (int, float)):
                            val = f"${v}"
                            if MONEY_REGEX.search(val):
                                return MONEY_REGEX.search(val).group(0)
                        if isinstance(v, str):
                            m = MONEY_REGEX.search(v)
                            if m:
                                return m.group(0)
                        # Recurse
                        mv = search_in_obj(v)
                        if mv:
                            return mv
                    else:
                        mv = search_in_obj(v)
                        if mv:
                            return mv
            elif isinstance(obj, list):
                for it in obj:
                    mv = search_in_obj(it)
                    if mv:
                        return mv
            elif isinstance(obj, str):
                if re.search(patterns_key, obj):
                    m = MONEY_REGEX.search(obj)
                    if m:
                        return m.group(0)
        except Exception:
            return None
        return None

    import json as _json

    for raw in candidates:
        raw = raw.strip()
        # First try strict JSON
        try:
            data = _json.loads(raw)
            mv = search_in_obj(data)
            if mv:
                return mv
        except Exception:
            pass
        # Fallback: find money near 7d/realized in raw text
        if re.search(patterns_key, raw):
            mm = MONEY_REGEX.search(raw)
            if mm:
                return mm.group(0)
    return None


def write_to_excel(result: Dict[str, Any]) -> None:
    """Write wallet and PnL data to profit.xlsx file"""
    excel_file = "profit.xlsx"
    
    # Extract wallet address from URL or use provided wallet
    wallet_address = result.get("wallet", "Unknown")
    if not wallet_address or wallet_address == "Unknown":
        # Try to extract from URL
        url = result.get("url", "")
        if url and "/address/" in url:
            wallet_address = url.split("/address/")[-1].split("?")[0]
        elif url and "gmgn.ai" in url:
            # Extract from gmgn.ai URL pattern - look for wallet addresses
            import re
            # Try different patterns for wallet addresses
            patterns = [
                r'/([a-zA-Z0-9]{32,44})',  # Standard wallet address length
                r'/([a-zA-Z0-9]{4,})',     # Fallback for shorter addresses
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    wallet_address = match.group(1)
                    break
    
    # Prepare data for Excel
    data = {
        "Wallet_Address": [wallet_address],
        "PnL_7D": [result.get("pnl_7d", 0.0)],
        "Currency": [result.get("currency", "USD")],
        "Text_Value": [result.get("text_value", "")],
        "Confidence": [result.get("confidence", 0.0)],
        "Strategy": [result.get("strategy", "")],
        "URL": [result.get("url", "")],
        "File": [result.get("file", "")]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Check if file exists to append or create new
    if Path(excel_file).exists():
        try:
            # Try to read existing file
            existing_df = pd.read_excel(excel_file, engine='openpyxl')
            # Ensure both DataFrames have the same columns
            for col in df.columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
            for col in existing_df.columns:
                if col not in df.columns:
                    df[col] = None
            # Reorder columns to match
            df = df.reindex(columns=existing_df.columns, fill_value=None)
            # Append new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_excel(excel_file, index=False, engine='openpyxl')
        except Exception:
            # If reading fails, create new file
            df.to_excel(excel_file, index=False, engine='openpyxl')
    else:
        # Create new file
        df.to_excel(excel_file, index=False, engine='openpyxl')
    
    print(f"Data written to {excel_file}")
    print(f"Wallet: {wallet_address}, PnL: {result.get('pnl_7d', 0.0)}")


def fetch_live_wallet_pnl(wallet_address: str, chain: str = "sol", headless: bool = True, debug: bool = False, cookies_file: Optional[str] = None, browser: str = "firefox") -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Fetch live PnL data from GMGN.ai for a given wallet address using Selenium.
    
    Args:
        wallet_address: The wallet address to check
        chain: Blockchain chain (sol, eth, etc.)
        headless: Whether to run browser in headless mode
        debug: Whether to print debug information
        cookies_file: Path to cookies file for authentication
        
    Returns:
        Tuple of (pnl_value, info_dict)
    """
    info: Dict[str, Any] = {"strategy": "live_selenium", "context": None}
    
    try:
        # Setup Firefox options with anti-detection measures
        firefox_options = FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        
        # Firefox anti-detection arguments for Cloudflare bypass
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--disable-extensions")
        firefox_options.add_argument("--disable-plugins")
        firefox_options.add_argument("--disable-images")
        firefox_options.add_argument("--window-size=1920,1080")
        firefox_options.add_argument("--disable-blink-features=AutomationControlled")
        firefox_options.add_argument("--disable-features=VizDisplayCompositor")
        firefox_options.add_argument("--disable-ipc-flooding-protection")
        firefox_options.add_argument("--disable-renderer-backgrounding")
        firefox_options.add_argument("--disable-backgrounding-occluded-windows")
        firefox_options.add_argument("--disable-client-side-phishing-detection")
        firefox_options.add_argument("--disable-sync")
        firefox_options.add_argument("--disable-translate")
        firefox_options.add_argument("--disable-logging")
        firefox_options.add_argument("--disable-gpu-logging")
        firefox_options.add_argument("--silent")
        firefox_options.add_argument("--log-level=3")
        
        # Advanced user agent rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
        ]
        import random
        selected_ua = random.choice(user_agents)
        firefox_options.set_preference("general.useragent.override", selected_ua)
        
        # Firefox-specific preferences for maximum stealth
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        firefox_options.set_preference("marionette.enabled", True)
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference("dom.push.enabled", False)
        firefox_options.set_preference("geo.enabled", False)
        firefox_options.set_preference("browser.search.suggest.enabled", False)
        firefox_options.set_preference("browser.urlbar.suggest.searches", False)
        firefox_options.set_preference("privacy.trackingprotection.enabled", False)
        firefox_options.set_preference("browser.safebrowsing.enabled", False)
        firefox_options.set_preference("browser.safebrowsing.malware.enabled", False)
        firefox_options.set_preference("browser.safebrowsing.phishing.enabled", False)
        firefox_options.set_preference("dom.event.clipboard.enabled", False)
        firefox_options.set_preference("media.navigator.enabled", False)
        firefox_options.set_preference("media.peerconnection.enabled", False)
        firefox_options.set_preference("webgl.disabled", True)
        firefox_options.set_preference("canvas.poisondata", True)
        firefox_options.set_preference("canvas.image.cache", False)
        
        # Initialize Firefox driver
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        # Execute advanced stealth JavaScript to bypass Cloudflare
        stealth_script = """
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {get: () => [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', filename: 'internal-nacl-plugin'}
        ]});
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome runtime
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {};
        }
        
        // Override getParameter to avoid detection
        const getParameter = WebGLRenderingContext.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
        
        // Mock screen properties
        Object.defineProperty(screen, 'availHeight', {get: () => 1040});
        Object.defineProperty(screen, 'availWidth', {get: () => 1920});
        Object.defineProperty(screen, 'colorDepth', {get: () => 24});
        Object.defineProperty(screen, 'height', {get: () => 1080});
        Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
        Object.defineProperty(screen, 'width', {get: () => 1920});
        
        // Mock timezone
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
            value: function() {
                return {timeZone: 'America/New_York'};
            }
        });
        """
        
        driver.execute_script(stealth_script)
        
        try:
            # First, navigate to GMGN.ai homepage to establish session
            if debug:
                print("Navigating to GMGN.ai homepage...")
            
            # Random delay to avoid detection
            import random
            time.sleep(random.uniform(2, 5))
            
            driver.get("https://gmgn.ai")
            
            # Wait for page to load with longer timeout for Cloudflare
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for Cloudflare challenge
            time.sleep(random.uniform(3, 7))
            
            # Check if Cloudflare challenge is present
            try:
                cloudflare_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Checking your browser') or contains(text(), 'Please wait') or contains(text(), 'DDoS protection')]")
                if cloudflare_elements:
                    if debug:
                        print("Cloudflare challenge detected, waiting...")
                    time.sleep(random.uniform(10, 20))
            except:
                pass
            
            # Check if we need to login
            login_required = False
            try:
                # Look for login button or sign-in elements
                login_elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Connect')]")
                if login_elements:
                    login_required = True
                    if debug:
                        print("Login required - found login button")
            except:
                pass
            
            # If cookies file provided, try to load cookies
            if cookies_file and Path(cookies_file).exists():
                if debug:
                    print(f"Loading cookies from {cookies_file}")
                try:
                    import json
                    with open(cookies_file, 'r') as f:
                        cookies = json.load(f)
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
                    if debug:
                        print("Cookies loaded successfully")
                except Exception as e:
                    if debug:
                        print(f"Failed to load cookies: {e}")
            
            # Navigate to the wallet page
            url = f"https://gmgn.ai/{chain}/address/{wallet_address}"
            if debug:
                print(f"Fetching wallet page: {url}")
            
            driver.get(url)
            
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check if we're redirected to login page
            current_url = driver.current_url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                if debug:
                    print("Redirected to login page - authentication required")
                info["error"] = "Authentication required - please login to GMGN.ai first"
                return None, info
            
            # Additional wait for dynamic content
            time.sleep(5)
            
            # Get page source
            html = driver.page_source
            
            if debug:
                print(f"Page loaded successfully, HTML length: {len(html)}")
            
            # Extract PnL using existing function
            value, extraction_info = extract_7d_realized_pnl_from_html(html, debug=debug)
            
            # Update info with extraction details
            info.update(extraction_info)
            info["url"] = url
            info["wallet_address"] = wallet_address
            info["chain"] = chain
            
            return value, info
            
        finally:
            driver.quit()
            
    except Exception as e:
        if debug:
            print(f"Error fetching live data: {e}")
        info["error"] = str(e)
        return None, info


def fetch_live_wallet_pnl_simple(wallet_address: str, chain: str = "sol", debug: bool = False) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Fetch live PnL data using simple HTTP requests (faster but may not work with Cloudflare).
    
    Args:
        wallet_address: The wallet address to check
        chain: Blockchain chain (sol, eth, etc.)
        debug: Whether to print debug information
        
    Returns:
        Tuple of (pnl_value, info_dict)
    """
    info: Dict[str, Any] = {"strategy": "live_requests", "context": None}
    
    try:
        # Construct URL
        url = f"https://gmgn.ai/{chain}/address/{wallet_address}"
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if debug:
            print(f"Fetching: {url}")
        
        # Make request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if debug:
            print(f"Response status: {response.status_code}, Content length: {len(response.text)}")
        
        # Extract PnL using existing function
        value, extraction_info = extract_7d_realized_pnl_from_html(response.text, debug=debug)
        
        # Update info with extraction details
        info.update(extraction_info)
        info["url"] = url
        info["wallet_address"] = wallet_address
        info["chain"] = chain
        
        return value, info
        
    except Exception as e:
        if debug:
            print(f"Error fetching live data: {e}")
        info["error"] = str(e)
        return None, info


def save_cookies(driver, cookies_file: str) -> None:
    """Save browser cookies to file for future authentication"""
    try:
        cookies = driver.get_cookies()
        import json
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f)
        print(f"Cookies saved to {cookies_file}")
    except Exception as e:
        print(f"Failed to save cookies: {e}")


def manual_browser_mode(wallet_address: str, chain: str = "sol", debug: bool = False) -> Tuple[Optional[float], Dict[str, Any]]:
    """Manual browser mode - user handles everything"""
    print("\n🌐 Manual Browser Mode")
    print("=" * 50)
    print("This will open a browser window where you can:")
    print("1. Login to GMGN.ai manually")
    print("2. Navigate to the wallet page")
    print("3. Save the HTML file")
    print("4. Use the HTML file with --html mode")
    print("=" * 50)
    
    # Setup Firefox with maximum stealth
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.add_argument("--disable-extensions")
    firefox_options.add_argument("--window-size=1920,1080")
    firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
    
    # Firefox stealth preferences
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference("useAutomationExtension", False)
    firefox_options.set_preference("marionette.enabled", True)
    firefox_options.set_preference("dom.webnotifications.enabled", False)
    firefox_options.set_preference("media.volume_scale", "0.0")
    
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    
    try:
        print("Opening browser...")
        driver.get(f"https://gmgn.ai/{chain}/address/{wallet_address}")
        
        print("\n📋 Instructions:")
        print("1. Login to GMGN.ai in the browser")
        print("2. Navigate to the wallet page if needed")
        print("3. Right-click and 'Save Page As' -> HTML file")
        print("4. Use the saved HTML file with --html mode")
        print("5. Press ENTER here when done...")
        
        input("Press ENTER when you have saved the HTML file...")
        
        # Try to get current page source
        html = driver.page_source
        if len(html) > 10000:  # Good amount of content
            print("✅ Page loaded successfully!")
            print(f"HTML length: {len(html)} characters")
            print("💡 You can now use this HTML with --html mode")
            
            # Try to extract PnL from current page
            value, info = extract_7d_realized_pnl_from_html(html, debug=debug)
            return value, info
        else:
            print("⚠️  Page content seems limited - you may need to login first")
            return None, {"error": "Manual login required", "strategy": "manual"}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, {"error": str(e), "strategy": "manual"}
    finally:
        driver.quit()


def interactive_login(driver, debug: bool = False) -> bool:
    """Interactive login process - user manually logs in"""
    print("\n🔐 GMGN.ai Authentication Required")
    print("=" * 50)
    print("Please login to GMGN.ai in the browser window that opened.")
    print("Steps:")
    print("1. Click 'Login' or 'Connect Wallet' button")
    print("2. Complete the login process (wallet connection, etc.)")
    print("3. Navigate to any wallet page to verify login")
    print("4. Press ENTER here when login is complete...")
    print("=" * 50)
    
    input("Press ENTER when you have completed login...")
    
    # Verify login by checking current page
    try:
        current_url = driver.current_url
        if debug:
            print(f"Current URL after login: {current_url}")
        
        # Check if we're on a wallet page or dashboard
        if "/address/" in current_url or "dashboard" in current_url.lower():
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login verification failed - please try again")
            return False
    except:
        print("❌ Could not verify login status")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract GMGN 7D Realized PnL from saved wallet HTML or live wallet data")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--html", help="Path to saved gmgn.ai wallet HTML file")
    mode_group.add_argument("--url", help="GMGN.ai wallet URL to fetch live data")
    mode_group.add_argument("--wallet-address", help="Wallet address to check live (e.g., 4eK5...RKVf)")
    
    # Common arguments
    parser.add_argument("--wallet", help="Wallet label/name (e.g., 4eK5...RKVf)")
    parser.add_argument("--chain", default="sol", help="Blockchain chain (sol, eth, etc.) - default: sol")
    parser.add_argument("--debug", action="store_true", help="Print debug info in JSON output")
    parser.add_argument("--excel", action="store_true", default=True, help="Write results to profit.xlsx file (default: True)")
    parser.add_argument("--no-excel", action="store_true", help="Disable Excel output")
    
    # Live mode specific arguments
    parser.add_argument("--selenium", action="store_true", help="Use Selenium for live data (handles Cloudflare)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode (default: True)")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    
    # Authentication arguments
    parser.add_argument("--cookies", help="Path to cookies file for authentication")
    parser.add_argument("--login", action="store_true", help="Interactive login mode (shows browser for manual login)")
    parser.add_argument("--save-cookies", help="Save cookies to file after login (e.g., --save-cookies cookies.json)")
    parser.add_argument("--manual", action="store_true", help="Manual browser mode - you handle login completely")
    parser.add_argument("--stealth", action="store_true", help="Use maximum stealth mode (slower but more likely to work)")
    parser.add_argument("--browser", choices=["firefox", "chrome"], default="firefox", help="Browser to use (default: firefox)")
    parser.add_argument("--cloudflare-bypass", action="store_true", help="Use advanced Cloudflare bypass techniques")
    parser.add_argument("--proxy", help="Use proxy server (format: ip:port)")
    parser.add_argument("--user-agent", help="Custom user agent string")
    
    args = parser.parse_args()

    # Determine wallet label
    wallet_label = args.wallet
    if not wallet_label:
        if args.wallet_address:
            wallet_label = args.wallet_address[:8] + "..." + args.wallet_address[-4:] if len(args.wallet_address) > 12 else args.wallet_address
        elif args.url:
            # Extract wallet from URL
            if "/address/" in args.url:
                wallet_address = args.url.split("/address/")[-1].split("?")[0]
                wallet_label = wallet_address[:8] + "..." + wallet_address[-4:] if len(wallet_address) > 12 else wallet_address
        else:
            wallet_label = "Unknown"

    # Extract PnL data based on mode
    if args.html:
        # HTML file mode
        html_path = Path(args.html)
        if not html_path.exists():
            raise SystemExit(f"HTML file not found: {html_path}")
        
        html = read_file_text(html_path)
        value, info = extract_7d_realized_pnl_from_html(html, debug=args.debug)
        
        result: Dict[str, Any] = {
            "wallet": wallet_label,
            "file": str(html_path),
            "url": None,
            "currency": "USD",
            "pnl_7d": value,
            "text_value": info.get("raw_money"),
            "confidence": 0.6 if value is not None else 0.0,
            "strategy": info.get("strategy"),
        }
        
    elif args.url:
        # URL mode - fetch live data
        if args.selenium:
            # Extract wallet address from URL for Selenium
            if "/address/" in args.url:
                wallet_address = args.url.split("/address/")[-1].split("?")[0]
                headless = args.headless and not args.no_headless
                value, info = fetch_live_wallet_pnl(wallet_address, chain=args.chain, headless=headless, debug=args.debug)
            else:
                raise SystemExit("Invalid URL format. Expected: https://gmgn.ai/sol/address/WALLET_ADDRESS")
        else:
            value, info = fetch_live_wallet_pnl_simple(args.url, chain=args.chain, debug=args.debug)
        
        result: Dict[str, Any] = {
            "wallet": wallet_label,
            "file": None,
            "url": args.url,
            "currency": "USD",
            "pnl_7d": value,
            "text_value": info.get("raw_money"),
            "confidence": 0.6 if value is not None else 0.0,
            "strategy": info.get("strategy"),
        }
        
    elif args.wallet_address:
        # Wallet address mode - fetch live data
        if args.selenium:
            # Handle manual mode
            if args.manual:
                value, info = manual_browser_mode(args.wallet_address, chain=args.chain, debug=args.debug)
            else:
                headless = args.headless and not args.no_headless
                
                # Handle interactive login
                if args.login:
                    print("🔐 Starting interactive login mode...")
                    headless = False  # Force visible browser for login
                    print("Browser will open for manual login...")
                
            value, info = fetch_live_wallet_pnl(
                args.wallet_address, 
                chain=args.chain, 
                headless=headless, 
                debug=args.debug,
                cookies_file=args.cookies,
                browser=args.browser
            )
            
            # Handle authentication errors
            if info.get("error") == "Authentication required - please login to GMGN.ai first":
                if args.login:
                    print("\n🔄 Attempting interactive login...")
                    # Re-run with visible browser for login
                    value, info = fetch_live_wallet_pnl(
                        args.wallet_address, 
                        chain=args.chain, 
                        headless=False, 
                        debug=args.debug,
                        cookies_file=args.cookies,
                        browser=args.browser
                    )
                else:
                    print("\n❌ Authentication required!")
                    print("💡 Try these options:")
                    print(f"   1. Manual mode: python gmgn_scrape.py --wallet-address {args.wallet_address} --selenium --manual")
                    print(f"   2. Interactive login: python gmgn_scrape.py --wallet-address {args.wallet_address} --selenium --login --debug")
                    print(f"   3. Stealth mode: python gmgn_scrape.py --wallet-address {args.wallet_address} --selenium --stealth --login")
                    print("💡 Or use saved cookies with --cookies cookies.json")
        else:
            value, info = fetch_live_wallet_pnl_simple(args.wallet_address, chain=args.chain, debug=args.debug)
        
        result: Dict[str, Any] = {
            "wallet": wallet_label,
            "file": None,
            "url": info.get("url"),
            "currency": "USD",
            "pnl_7d": value,
            "text_value": info.get("raw_money"),
            "confidence": 0.6 if value is not None else 0.0,
            "strategy": info.get("strategy"),
        }
    
    if args.debug:
        result["debug_context"] = info.get("context")
    
    # Write to Excel if requested (default behavior unless --no-excel is specified)
    if args.excel and not args.no_excel:
        write_to_excel(result)
    
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()


