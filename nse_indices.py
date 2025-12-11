"""
NSE Indices Stock List Manager
Fetches and caches Nifty 50, Nifty Next 50, and Nifty 500 stock lists
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Cache file paths
CACHE_DIR = 'nse_cache'
NIFTY50_CACHE = os.path.join(CACHE_DIR, 'nifty50.json')
NIFTYNEXT50_CACHE = os.path.join(CACHE_DIR, 'niftynext50.json')
NIFTY500_CACHE = os.path.join(CACHE_DIR, 'nifty500.json')

# Cache validity (refresh daily)
CACHE_VALIDITY_HOURS = 24

# NSE official URLs for index constituents
NSE_URLS = {
    'NIFTY50': 'https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv',
    'NIFTYNEXT50': 'https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv',
    'NIFTY500': 'https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv'
}

def ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"✅ Created cache directory: {CACHE_DIR}")

def is_cache_valid(cache_file):
    """Check if cache file exists and is still valid"""
    if not os.path.exists(cache_file):
        return False
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            cached_time = datetime.fromisoformat(data['cached_at'])
            age = datetime.now() - cached_time
            return age.total_seconds() < (CACHE_VALIDITY_HOURS * 3600)
    except Exception as e:
        print(f"⚠️ Cache validation error: {e}")
        return False

def parse_nse_csv(csv_text):
    """Parse NSE CSV data and extract stock information"""
    lines = csv_text.strip().split('\n')
    stocks = []
    
    # Skip header and empty lines
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            try:
                stock = {
                    'company_name': parts[0],
                    'nse_symbol': parts[2],
                    'industry': parts[1] if len(parts) > 1 else 'Unknown'
                }
                stocks.append(stock)
            except Exception as e:
                continue
    
    return stocks

def fetch_index_from_nse(index_name):
    """Fetch index constituents from NSE website"""
    url = NSE_URLS.get(index_name)
    if not url:
        print(f"❌ Unknown index: {index_name}")
        return None
    
    try:
        print(f"📡 Fetching {index_name} from NSE...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        stocks = parse_nse_csv(response.text)
        
        if stocks:
            print(f"✅ Fetched {len(stocks)} stocks from {index_name}")
            return {
                'index_name': index_name,
                'stocks': stocks,
                'count': len(stocks),
                'cached_at': datetime.now().isoformat(),
                'source': 'NSE India'
            }
        else:
            print(f"⚠️ No stocks found in {index_name}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching {index_name}: {str(e)}")
        return None

def save_to_cache(data, cache_file):
    """Save index data to cache file"""
    try:
        ensure_cache_dir()
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Cached to: {cache_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving cache: {e}")
        return False

def load_from_cache(cache_file):
    """Load index data from cache file"""
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return None

def get_index_stocks(index_name, cache_file):
    """Get index stocks with caching"""
    # Try cache first
    if is_cache_valid(cache_file):
        print(f"📂 Loading {index_name} from cache...")
        data = load_from_cache(cache_file)
        if data:
            print(f"✅ Loaded {data['count']} stocks from cache")
            return data
    
    # Fetch from NSE
    data = fetch_index_from_nse(index_name)
    if data:
        save_to_cache(data, cache_file)
    
    return data

def get_nifty50():
    """Get Nifty 50 stocks"""
    return get_index_stocks('NIFTY50', NIFTY50_CACHE)

def get_niftynext50():
    """Get Nifty Next 50 stocks"""
    return get_index_stocks('NIFTYNEXT50', NIFTYNEXT50_CACHE)

def get_nifty500():
    """Get Nifty 500 stocks"""
    return get_index_stocks('NIFTY500', NIFTY500_CACHE)

def get_all_indices():
    """Get all NSE indices"""
    return {
        'nifty50': get_nifty50(),
        'niftynext50': get_niftynext50(),
        'nifty500': get_nifty500()
    }

def create_symbol_lookup():
    """Create a lookup dictionary for quick checking if a symbol is in any index"""
    all_data = get_all_indices()
    lookup = {}
    
    for index_name, data in all_data.items():
        if data and 'stocks' in data:
            for stock in data['stocks']:
                symbol = stock['nse_symbol']
                if symbol not in lookup:
                    lookup[symbol] = []
                lookup[symbol].append(index_name.upper())
    
    return lookup

def is_in_index(nse_symbol, index_name):
    """Check if a stock is in a specific index"""
    index_name = index_name.upper()
    
    cache_files = {
        'NIFTY50': NIFTY50_CACHE,
        'NIFTYNEXT50': NIFTYNEXT50_CACHE,
        'NIFTY500': NIFTY500_CACHE
    }
    
    cache_file = cache_files.get(index_name)
    if not cache_file:
        return False
    
    data = get_index_stocks(index_name, cache_file)
    if not data or 'stocks' not in data:
        return False
    
    return any(stock['nse_symbol'] == nse_symbol for stock in data['stocks'])

if __name__ == '__main__':
    """Test the module"""
    print("=" * 80)
    print("NSE Indices Stock List Fetcher")
    print("=" * 80)
    
    # Fetch all indices
    indices = get_all_indices()
    
    # Print summary
    for index_name, data in indices.items():
        if data:
            print(f"\n{index_name.upper()}: {data['count']} stocks")
            print(f"Cached at: {data['cached_at']}")
    
    # Create lookup
    print("\n" + "=" * 80)
    print("Creating symbol lookup...")
    lookup = create_symbol_lookup()
    print(f"✅ Total unique symbols: {len(lookup)}")
    
    # Test a few symbols
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK']
    print("\n" + "=" * 80)
    print("Testing some symbols:")
    for symbol in test_symbols:
        if symbol in lookup:
            print(f"  {symbol}: {', '.join(lookup[symbol])}")
