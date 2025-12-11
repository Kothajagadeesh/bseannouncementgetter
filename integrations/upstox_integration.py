"""
Upstox API Integration Module
Handles authentication and live market data fetching from Upstox
"""

import requests
import json
import os
from datetime import datetime

# Upstox API Configuration
UPSTOX_API_BASE = "https://api.upstox.com/v2"
ACCESS_TOKEN = None

# F&O Eligible Stock Instrument Keys (NSE)
# Total: 77 stocks out of 83 F&O eligible stocks
# Generated: 2025-12-11
STOCK_INSTRUMENT_KEYS = {
    'ACC': 'NSE_EQ|INE012A01025',
    'ADANIENT': 'NSE_EQ|INE423A01024',
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'AMBUJACEM': 'NSE_EQ|INE079A01024',
    'APOLLOHOSP': 'NSE_EQ|INE437A01024',
    'ASIANPAINT': 'NSE_EQ|INE021A01026',
    'AUROPHARMA': 'NSE_EQ|INE406A01037',
    'AXISBANK': 'NSE_EQ|INE238A01034',
    'BAJAJ-AUTO': 'NSE_EQ|INE917I01010',
    'BAJAJFINSV': 'NSE_EQ|INE918I01018',
    'BAJFINANCE': 'NSE_EQ|INE296A01024',
    'BANDHANBNK': 'NSE_EQ|INE545U01014',
    'BERGEPAINT': 'NSE_EQ|INE463A01038',
    'BHARATFORG': 'NSE_EQ|INE465A01025',
    'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'BOSCHLTD': 'NSE_EQ|INE323A01026',
    'BPCL': 'NSE_EQ|INE029A01011',
    'BRITANNIA': 'NSE_EQ|INE216A01030',
    'CANBK': 'NSE_EQ|INE476A01022',
    'CIPLA': 'NSE_EQ|INE059A01026',
    'COALINDIA': 'NSE_EQ|INE522F01014',
    'COFORGE': 'NSE_EQ|INE591G01017',
    'DIVISLAB': 'NSE_EQ|INE361B01024',
    'DLF': 'NSE_EQ|INE271C01023',
    'DRREDDY': 'NSE_EQ|INE089A01023',
    'EICHERMOT': 'NSE_EQ|INE066A01021',
    'GODREJCP': 'NSE_EQ|INE102D01028',
    'GRASIM': 'NSE_EQ|INE047A01021',
    'HAVELLS': 'NSE_EQ|INE176B01034',
    'HCLTECH': 'NSE_EQ|INE860A01027',
    'HDFCBANK': 'NSE_EQ|INE040A01034',
    'HDFCLIFE': 'NSE_EQ|INE795G01014',
    'HEROMOTOCO': 'NSE_EQ|INE158A01026',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'HINDUNILVR': 'NSE_EQ|INE030A01027',
    'ICICIBANK': 'NSE_EQ|INE090A01021',
    'ICICIPRULI': 'NSE_EQ|INE726G01019',
    'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'INFY': 'NSE_EQ|INE009A01021',
    'IOC': 'NSE_EQ|INE242A01010',
    'ITC': 'NSE_EQ|INE154A01025',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'JUBLFOOD': 'NSE_EQ|INE797F01020',
    'KOTAKBANK': 'NSE_EQ|INE237A01028',
    'LICHSGFIN': 'NSE_EQ|INE115A01026',
    'LT': 'NSE_EQ|INE018A01030',
    'LUPIN': 'NSE_EQ|INE326A01037',
    'M&M': 'NSE_EQ|INE101A01026',
    'MARUTI': 'NSE_EQ|INE585B01010',
    'MOTHERSON': 'NSE_EQ|INE775A01035',
    'MPHASIS': 'NSE_EQ|INE356A01018',
    'NESTLEIND': 'NSE_EQ|INE239A01016',
    'NTPC': 'NSE_EQ|INE733E01010',
    'ONGC': 'NSE_EQ|INE213A01029',
    'PAYTM': 'NSE_EQ|INE982J01020',
    'PERSISTENT': 'NSE_EQ|INE262H01013',
    'PIDILITIND': 'NSE_EQ|INE318A01026',
    'PNB': 'NSE_EQ|INE160A01022',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'SBILIFE': 'NSE_EQ|INE123W01016',
    'SBIN': 'NSE_EQ|INE062A01020',
    'SHREECEM': 'NSE_EQ|INE070A01015',
    'SIEMENS': 'NSE_EQ|INE003A01024',
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'TATAPOWER': 'NSE_EQ|INE245A01021',
    'TATASTEEL': 'NSE_EQ|INE081A01020',
    'TCS': 'NSE_EQ|INE467B01029',
    'TECHM': 'NSE_EQ|INE669C01036',
    'TITAN': 'NSE_EQ|INE280A01028',
    'TORNTPHARM': 'NSE_EQ|INE685A01028',
    'TORNTPOWER': 'NSE_EQ|INE813H01021',
    'ULTRACEMCO': 'NSE_EQ|INE481G01011',
    'VEDL': 'NSE_EQ|INE205A01025',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'ZOMATO': 'NSE_EQ|INE758T01015',
}

class UpstoxAPI:
    def __init__(self, api_key=None, api_secret=None, access_token=None):
        """Initialize Upstox API client"""
        self.api_key = api_key or os.environ.get('UPSTOX_API_KEY')
        self.api_secret = api_secret or os.environ.get('UPSTOX_API_SECRET')
        self.access_token = access_token or os.environ.get('UPSTOX_ACCESS_TOKEN')
        self.base_url = UPSTOX_API_BASE
        
    def get_authorization_url(self, redirect_uri):
        """Generate authorization URL for user login"""
        auth_url = f"https://api.upstox.com/v2/login/authorization/dialog"
        params = {
            'response_type': 'code',
            'client_id': self.api_key,
            'redirect_uri': redirect_uri
        }
        url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{url_params}"
    
    def get_access_token(self, auth_code, redirect_uri):
        """Exchange authorization code for access token"""
        url = f"{self.base_url}/login/authorization/token"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'code': auth_code,
            'client_id': self.api_key,
            'client_secret': self.api_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
            self.access_token = result.get('access_token')
            return result
        except Exception as e:
            print(f"Error getting access token: {str(e)}")
            return None
    
    def get_market_quote(self, symbol, exchange='NSE'):
        """Get real-time market quote for a symbol"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        # Format: NSE_EQ|INE009A01021 or NSE_FO|NIFTY23NOVFUT
        instrument_key = f"{exchange}_EQ|{symbol}"
        
        url = f"{self.base_url}/market-quote/quotes"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'instrument_key': instrument_key
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching market quote: {str(e)}")
            return {'error': str(e)}
    
    def search_instruments(self, query):
        """Search for instrument keys by symbol"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        url = f"{self.base_url}/market-quote/instruments"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'symbol': query,
            'exchange': 'NSE'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == 'success' and data.get('data'):
                # Return the first matching instrument key
                return data['data'][0]['instrument_key'] if data['data'] else None
            return None
        except Exception as e:
            print(f"Error searching instrument: {str(e)}")
            return None
    
    def get_market_quotes_multiple(self, symbols, exchange='NSE'):
        """Get real-time market quotes for multiple symbols"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        # Get instrument keys from mapping
        instrument_keys = []
        for symbol in symbols:
            symbol_upper = symbol.upper().strip()
            if symbol_upper in STOCK_INSTRUMENT_KEYS:
                instrument_key = STOCK_INSTRUMENT_KEYS[symbol_upper]
                instrument_keys.append(instrument_key)
                print(f"Found instrument key for {symbol}: {instrument_key}")
            else:
                print(f"Symbol {symbol} not in mapping. Add it to STOCK_INSTRUMENT_KEYS.")
        
        if not instrument_keys:
            return {'error': 'No valid instrument keys found. Symbols must be in the predefined list.', 'data': {}}
        
        url = f"{self.base_url}/market-quote/quotes"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'instrument_key': ','.join(instrument_keys)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching market quotes: {str(e)}")
            print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            return {'error': str(e), 'data': {}}
    
    def get_quotes_by_instrument_keys(self, instrument_keys):
        """Get market quotes using instrument keys directly (for options, futures, etc.)"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        if not instrument_keys:
            return {'error': 'No instrument keys provided', 'data': {}}
        
        # Upstox API allows max 500 instruments per request
        if len(instrument_keys) > 500:
            print(f"⚠️ Warning: {len(instrument_keys)} keys provided, only processing first 500")
            instrument_keys = instrument_keys[:500]
        
        url = f"{self.base_url}/market-quote/quotes"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'instrument_key': ','.join(instrument_keys)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching quotes by instrument keys: {str(e)}")
            if 'response' in locals():
                print(f"Response text: {response.text[:500]}")
            return {'error': str(e), 'data': {}}
    
    def get_ohlc(self, symbol, exchange='NSE', interval='1day'):
        """Get OHLC (Open, High, Low, Close) data"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        instrument_key = f"{exchange}_EQ|{symbol}"
        
        url = f"{self.base_url}/market-quote/ohlc"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'instrument_key': instrument_key,
            'interval': interval
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching OHLC data: {str(e)}")
            return {'error': str(e)}
    
    def get_user_profile(self):
        """Get user profile information"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        url = f"{self.base_url}/user/profile"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
            return {'error': str(e)}
    
    def search_instrument(self, query):
        """Search for instruments/symbols"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        url = f"{self.base_url}/market-quote/instruments/search"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'query': query
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching instruments: {str(e)}")
            return {'error': str(e)}
    
    def get_next_expiry_date(self):
        """Calculate next monthly expiry date (last Thursday of current/next month)"""
        from datetime import datetime, timedelta
        import calendar
        
        today = datetime.now()
        
        # Start with current month
        year = today.year
        month = today.month
        
        # Get last day of the month
        last_day = calendar.monthrange(year, month)[1]
        
        # Find last Thursday
        for day in range(last_day, 0, -1):
            date = datetime(year, month, day)
            if date.weekday() == 3:  # Thursday is 3
                # If the expiry is in the past, move to next month
                if date < today:
                    # Move to next month
                    if month == 12:
                        year += 1
                        month = 1
                    else:
                        month += 1
                    last_day = calendar.monthrange(year, month)[1]
                    for day in range(last_day, 0, -1):
                        date = datetime(year, month, day)
                        if date.weekday() == 3:
                            return date.strftime('%Y-%m-%d')
                else:
                    return date.strftime('%Y-%m-%d')
        
        return today.strftime('%Y-%m-%d')
    
    def get_options_chain(self, symbol, expiry_date=None):
        """Get options chain (all CE/PE) for a symbol"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        # Get instrument key for the symbol
        if symbol not in STOCK_INSTRUMENT_KEYS:
            return {'error': f'Symbol {symbol} not in supported list'}
        
        instrument_key = STOCK_INSTRUMENT_KEYS[symbol]
        
        # If no expiry date provided, calculate next expiry
        if not expiry_date:
            expiry_date = self.get_next_expiry_date()
        
        url = f"{self.base_url}/option/chain"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'instrument_key': instrument_key,
            'expiry_date': expiry_date  # REQUIRED parameter
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching options chain for {symbol} (expiry: {expiry_date}): {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {'error': str(e)}
    
    def get_all_fo_options_summary(self):
        """Get options summary for ALL F&O stocks"""
        if not self.access_token:
            return {'error': 'Not authenticated. Please login first.'}
        
        # Get ALL F&O stocks (77 stocks)
        all_symbols = list(STOCK_INSTRUMENT_KEYS.keys())
        
        print(f"\n📊 Fetching options data for {len(all_symbols)} F&O stocks...")
        
        options_data = {}
        success_count = 0
        error_count = 0
        
        for i, symbol in enumerate(all_symbols, 1):
            print(f"  [{i}/{len(all_symbols)}] Fetching {symbol}...", end=' ')
            chain = self.get_options_chain(symbol)
            if not chain.get('error'):
                options_data[symbol] = chain
                success_count += 1
                print("✅")
            else:
                error_count += 1
                print(f"❌ {chain.get('error')}")
        
        print(f"\n📈 Summary: {success_count} successful, {error_count} failed out of {len(all_symbols)} stocks\n")
        
        return options_data


# Global Upstox client instance
upstox_client = UpstoxAPI()


def is_authenticated():
    """Check if Upstox is authenticated"""
    return upstox_client.access_token is not None


def get_live_data_for_announcements(announcements):
    """Enrich announcements with live market data from Upstox"""
    if not is_authenticated():
        print("⚠️ Upstox not authenticated. Skipping live data enrichment.")
        return announcements
    
    # Extract NSE symbols
    symbols = []
    for ann in announcements:
        if ann.get('nse_symbol'):
            symbols.append(ann['nse_symbol'])
    
    if not symbols:
        return announcements
    
    # Fetch live data for all symbols
    print(f"📊 Fetching live data for {len(symbols)} symbols from Upstox...")
    live_data = upstox_client.get_market_quotes_multiple(symbols[:50])  # Max 50 at a time
    
    if live_data.get('error'):
        print(f"❌ Error fetching live data: {live_data['error']}")
        return announcements
    
    # Enrich announcements with live data
    data_map = {}
    if live_data.get('data'):
        for key, value in live_data['data'].items():
            # Extract symbol from key
            symbol = key.split('|')[1] if '|' in key else key
            data_map[symbol] = value
    
    for ann in announcements:
        nse_symbol = ann.get('nse_symbol')
        if nse_symbol and nse_symbol in data_map:
            quote = data_map[nse_symbol]
            ann['live_data'] = {
                'ltp': quote.get('last_price'),
                'change': quote.get('net_change'),
                'change_percent': quote.get('pct_change'),
                'volume': quote.get('volume'),
                'open': quote.get('ohlc', {}).get('open'),
                'high': quote.get('ohlc', {}).get('high'),
                'low': quote.get('ohlc', {}).get('low'),
                'close': quote.get('ohlc', {}).get('close')
            }
    
    return announcements


if __name__ == '__main__':
    """Test the Upstox integration"""
    print("=" * 80)
    print("Upstox API Integration Test")
    print("=" * 80)
    
    # Check if credentials are set
    if not upstox_client.api_key:
        print("\n⚠️ UPSTOX_API_KEY not set in environment variables")
    else:
        print(f"\n✅ API Key found: {upstox_client.api_key[:10]}...")
    
    if not upstox_client.access_token:
        print("⚠️ UPSTOX_ACCESS_TOKEN not set. You need to authenticate first.")
        print("\nTo authenticate:")
        print("1. Set UPSTOX_API_KEY and UPSTOX_API_SECRET environment variables")
        print("2. Run the Flask app and visit /upstox/login")
        print("3. Complete the OAuth flow")
    else:
        print(f"✅ Access Token found")
        
        # Test getting user profile
        print("\n📊 Testing User Profile API...")
        profile = upstox_client.get_user_profile()
        print(json.dumps(profile, indent=2))
