# 🛡️ Cloudflare Bypass Solutions for GMGN.ai

## The Problem
GMGN.ai uses Cloudflare protection which blocks automated browsers and requires human verification.

## 🚀 **Immediate Solutions (Recommended)**

### 1. **Manual Browser Method** ⭐ **BEST OPTION**
```bash
# Use manual mode - you handle everything
python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --manual --browser firefox
```
**Steps:**
1. Browser opens automatically
2. You login manually (no automation detection)
3. Navigate to wallet page
4. Save HTML file
5. Use HTML file with scraper

### 2. **Alternative Data Sources** ⭐ **RELIABLE**
Instead of GMGN.ai, use these alternatives:

#### **Solscan.io** (Recommended)
```bash
# Visit: https://solscan.io/account/YOUR_WALLET
# Save the page as HTML
python gmgn_scrape.py --html "solscan_saved.html" --wallet "My_Wallet" --debug
```

#### **SolanaFM**
```bash
# Visit: https://solana.fm/account/YOUR_WALLET
# Save the page as HTML
python gmgn_scrape.py --html "solanafm_saved.html" --wallet "My_Wallet" --debug
```

#### **Birdeye**
```bash
# Visit: https://birdeye.so/portfolio/YOUR_WALLET
# Save the page as HTML
python gmgn_scrape.py --html "birdeye_saved.html" --wallet "My_Wallet" --debug
```

### 3. **VPN + Manual Browser**
1. Connect to VPN (different country)
2. Use manual browser mode
3. Login normally
4. Save HTML file

### 4. **Mobile Browser Method**
1. Open Chrome on your phone
2. Go to GMGN.ai
3. Login normally
4. Navigate to wallet page
5. Share page to computer
6. Save as HTML

## 🔧 **Advanced Solutions**

### 5. **Residential Proxies**
```bash
# Use residential proxy service
python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --proxy "proxy_ip:port" --browser firefox
```

### 6. **Different Time Zones**
- Try accessing during off-peak hours
- Use VPN to different time zones
- Access during weekends

### 7. **Browser Extensions**
- Install "User-Agent Switcher" extension
- Switch to mobile user agent
- Disable JavaScript temporarily

## 📱 **Mobile App Alternative**
- Download GMGN.ai mobile app
- Login normally
- Take screenshots of PnL data
- Use OCR to extract data

## 🔄 **Automated Alternatives**

### **API-Based Solutions**
```python
# Use Solana RPC directly
import requests

def get_wallet_data(wallet_address):
    url = "https://api.mainnet-beta.solana.com"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [wallet_address, {"encoding": "base64"}]
    }
    response = requests.post(url, json=payload)
    return response.json()
```

### **Third-Party APIs**
- **Helius API**: https://helius.xyz/
- **QuickNode**: https://quicknode.com/
- **Alchemy**: https://alchemy.com/

## 🎯 **Recommended Workflow**

### **For Regular Use:**
1. **Use Solscan.io** (most reliable)
2. Save HTML files manually
3. Use scraper with HTML files
4. Automate the HTML processing

### **For GMGN.ai Specifically:**
1. **Manual browser mode** with VPN
2. Save cookies after login
3. Use saved cookies for future runs
4. Rotate between different methods

## 🚨 **Important Notes**

- **Cloudflare is very aggressive** - automated bypass is difficult
- **Manual methods work best** - no automation detection
- **Alternative sites are often better** - less protection
- **VPN helps** - changes your IP fingerprint
- **Mobile browsers work better** - less detection

## 💡 **Quick Commands**

```bash
# Manual mode (recommended)
python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --manual --browser firefox

# With VPN (if you have proxy)
python gmgn_scrape.py --wallet-address "YOUR_WALLET" --selenium --proxy "your_proxy:port" --browser firefox

# Alternative site (Solscan)
# 1. Visit https://solscan.io/account/YOUR_WALLET
# 2. Save as HTML
python gmgn_scrape.py --html "solscan.html" --wallet "My_Wallet" --debug
```

## 🔍 **Detection Methods**

Cloudflare detects:
- Automated browser signatures
- Missing human-like behavior
- Rapid requests
- Missing browser plugins
- Suspicious user agents
- IP reputation

## ✅ **Success Indicators**

- HTML length > 50,000 characters
- Contains actual wallet data
- No "Checking your browser" messages
- PnL values extracted successfully

Choose the method that works best for your situation!
