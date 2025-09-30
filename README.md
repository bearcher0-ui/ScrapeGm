GMGN 7D Realized PnL Scraper

This small utility extracts the 7D Realized PnL from a saved gmgn.ai wallet HTML page.

Prerequisites
- Python 3.9+

Setup
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Usage Modes

### 1. HTML File Mode (Original)
```bash
python gmgn_scrape.py --html "<path to saved HTML>" --wallet "<label>" --debug
```

### 2. Live Wallet Address Mode (NEW!)
```bash
# ⚠️ IMPORTANT: GMGN.ai requires login for live data access

# Interactive login mode with Firefox (recommended for first time)
python gmgn_scrape.py --wallet-address "4eK5n4LUoCHbxyrem1erKHPAbzajv76g2jNxopTYRKVf" --wallet "4eK5...RKVf" --selenium --browser firefox --login --debug

# Using saved cookies (after initial login)
python gmgn_scrape.py --wallet-address "4eK5n4LUoCHbxyrem1erKHPAbzajv76g2jNxopTYRKVf" --wallet "4eK5...RKVf" --selenium --browser firefox --cookies gmgn_cookies.json --debug

# With custom chain
python gmgn_scrape.py --wallet-address "0x1234..." --wallet "ETH_Wallet" --chain eth --selenium --login --debug
```

### 3. Live URL Mode (NEW!)
```bash
# Direct URL with Selenium
python gmgn_scrape.py --url "https://gmgn.ai/sol/address/4eK5n4LUoCHbxyrem1erKHPAbzajv76g2jNxopTYRKVf" --wallet "4eK5...RKVf" --selenium --debug
```

### 4. Legacy Modes (Still Supported)
```bash
# Text file containing URL
python gmgn_scrape.py --html "Website.txt" --wallet "<label>" --debug

# Text file containing wallet address
python gmgn_scrape.py --html "Website.txt" --wallet "<label>" --chain sol --debug
```

## Live Mode Options

### Selenium Options
- `--selenium`: Use Selenium for live data (handles Cloudflare protection)
- `--headless`: Run browser in headless mode (default: True)
- `--no-headless`: Show browser window (useful for debugging)

### Chain Support
- `--chain sol`: Solana (default)
- `--chain eth`: Ethereum
- Other chains supported by GMGN.ai

## 🔐 Authentication Required for Live Data

**IMPORTANT**: GMGN.ai requires login to access wallet data. The scraper now includes authentication support.

### First Time Setup (Interactive Login)

1. **Run with login flag:**
   ```bash
   python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --login --debug
   ```

2. **Complete login in browser:**
   - Browser window will open
   - Login to GMGN.ai manually
   - Connect your wallet if required
   - Navigate to any wallet page to verify

3. **Save cookies for future use:**
   ```bash
   python save_cookies.py gmgn_cookies.json
   ```

### Using Saved Cookies (Faster)

After initial login, use saved cookies:
```bash
python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --cookies gmgn_cookies.json --debug
```

### Authentication Options

- `--login`: Interactive login mode (shows browser)
- `--cookies FILE`: Use saved cookies file
- `--save-cookies FILE`: Save cookies after login
- `--no-headless`: Show browser window (useful for debugging)

### Browser Options
- `--browser firefox`: Use Firefox (default, recommended for bypassing blocks)
- `--browser chrome`: Use Chrome (may be more blocked)

### Notes
- Firefox is the default browser (less likely to be blocked)
- First run downloads GeckoDriver (Firefox) or ChromeDriver automatically
- Selenium mode is required for live data (handles Cloudflare + authentication)
- Cookies expire periodically - re-login when needed
- Simple HTTP mode doesn't work with GMGN.ai (authentication required)

## Examples

### HTML File Example
```bash
python gmgn_scrape.py --html "4eK5...RKVf 30D Realized Profit -$189.52(-0.02X) - GMGN.AI Fast Trade, Fast Copy Trade, Fast AFK Automation.htm" --wallet "4eK5...RKVf" --debug
```

### Live Wallet Example
```bash
# Check live PnL for a Solana wallet
python gmgn_scrape.py --wallet-address "4eK5n4LUoCHbxyrem1erKHPAbzajv76g2jNxopTYRKVf" --wallet "4eK5...RKVf" --selenium --debug

# Check live PnL for an Ethereum wallet
python gmgn_scrape.py --wallet-address "0x1234567890abcdef..." --wallet "ETH_Wallet" --chain eth --selenium --debug
```

Output
Prints a single JSON object, for example:
```json
{
  "wallet": "4eK5...RKVf",
  "file": "...",
  "currency": "USD",
  "pnl_7d": -284.68,
  "text_value": "-$284.68",
  "confidence": 0.6,
  "strategy": "analysis_card_keywords",
  "debug_context": "..."
}
```

Notes
- The parser uses heuristics and may need adjustment if gmgn.ai changes its UI.
- If it fails to find a value, `pnl_7d` will be null.

