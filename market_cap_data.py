"""
Market Cap Classification Module
Fetches and determines market cap category for BSE listed companies
"""
import requests
import json

def get_market_cap_category(bse_code):
    """
    Determine market cap category for a company
    
    Categories:
    - Large Cap: Market cap >= 20,000 Cr
    - Mid Cap: Market cap >= 5,000 Cr and < 20,000 Cr
    - Small Cap: Market cap >= 500 Cr and < 5,000 Cr
    - Micro Cap: Market cap < 500 Cr
    """
    try:
        # Try to fetch from BSE API
        url = f"https://api.bseindia.com/BseIndiaAPI/api/ComHeadernew/w"
        params = {
            'quotetype': 'EQ',
            'scripcode': bse_code,
            'seriesid': ''
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.bseindia.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract market cap (in Crores)
            market_cap_str = data.get('MktCap', '0')
            
            # Clean and convert market cap
            market_cap = parse_market_cap(market_cap_str)
            
            # Classify
            return classify_market_cap(market_cap)
        
    except Exception as e:
        print(f"Error fetching market cap for {bse_code}: {str(e)}")
    
    return 'Unknown'

def parse_market_cap(market_cap_str):
    """Parse market cap string to float (in Crores)"""
    try:
        # Remove commas and convert to float
        market_cap_str = str(market_cap_str).replace(',', '').strip()
        
        if not market_cap_str or market_cap_str == '0':
            return 0
        
        return float(market_cap_str)
    except:
        return 0

def classify_market_cap(market_cap_crores):
    """Classify market cap into categories"""
    if market_cap_crores >= 20000:
        return {
            'category': 'Large Cap',
            'emoji': '🟢',
            'color': '#10b981'
        }
    elif market_cap_crores >= 5000:
        return {
            'category': 'Mid Cap',
            'emoji': '🟡',
            'color': '#f59e0b'
        }
    elif market_cap_crores >= 500:
        return {
            'category': 'Small Cap',
            'emoji': '🟠',
            'color': '#f97316'
        }
    elif market_cap_crores > 0:
        return {
            'category': 'Micro Cap',
            'emoji': '🔴',
            'color': '#ef4444'
        }
    else:
        return {
            'category': 'Unknown',
            'emoji': '⚪',
            'color': '#9ca3af'
        }

# Cache for market cap data (to avoid repeated API calls)
market_cap_cache = {}

def get_market_cap_with_cache(bse_code):
    """Get market cap with caching"""
    if bse_code in market_cap_cache:
        return market_cap_cache[bse_code]
    
    result = get_market_cap_category(bse_code)
    market_cap_cache[bse_code] = result
    return result
