#!/usr/bin/env python3
"""
Update F&O stocks list from NSE India official API
"""

import requests
import json
from datetime import datetime

def fetch_nse_fo_stocks():
    """Fetch F&O stocks from NSE India API"""
    url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        print("📥 Fetching F&O stocks from NSE India...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        stocks_data = data.get('data', [])
        
        print(f"✅ Found {len(stocks_data)} F&O stocks from NSE")
        
        return stocks_data
    except Exception as e:
        print(f"❌ Error fetching NSE data: {str(e)}")
        return []

def update_fo_stocks_json(nse_stocks):
    """Update fo_stocks.json with NSE data"""
    
    # Transform NSE data to our format
    fo_stocks = []
    
    for stock in nse_stocks:
        symbol = stock.get('symbol', '')
        company_name = stock.get('meta', {}).get('companyName', '')
        isin = stock.get('meta', {}).get('isin', '')
        
        # Skip if no symbol
        if not symbol:
            continue
        
        fo_stocks.append({
            'nse_symbol': symbol,
            'company_name': company_name,
            'isin': isin,
            'bse_code': '',  # Will be populated later if available
            'sector': stock.get('meta', {}).get('industry', 'Unknown')
        })
    
    # Sort by NSE symbol
    fo_stocks.sort(key=lambda x: x['nse_symbol'])
    
    # Create output structure
    output = {
        'metadata': {
            'source': 'NSE India Official API',
            'url': 'https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(fo_stocks)
        },
        'stocks': fo_stocks
    }
    
    # Write to file
    output_file = 'fo_stocks_nse.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved {len(fo_stocks)} stocks to {output_file}")
    
    # Print comparison
    print(f"\n📊 Comparison:")
    try:
        with open('fo_stocks.json', 'r') as f:
            old_data = json.load(f)
            old_count = len(old_data.get('stocks', []))
            print(f"   Old list: {old_count} stocks")
            print(f"   New list: {len(fo_stocks)} stocks")
            print(f"   Difference: +{len(fo_stocks) - old_count} stocks")
    except FileNotFoundError:
        print(f"   Old fo_stocks.json not found")
    
    # Show new stocks
    print(f"\n📝 First 20 stocks:")
    for i, stock in enumerate(fo_stocks[:20], 1):
        print(f"   {i}. {stock['nse_symbol']} - {stock['company_name']}")
    
    return output

if __name__ == "__main__":
    print("=" * 80)
    print("NSE F&O Stocks Updater")
    print("=" * 80)
    
    # Fetch from NSE
    nse_stocks = fetch_nse_fo_stocks()
    
    if nse_stocks:
        # Update JSON file
        result = update_fo_stocks_json(nse_stocks)
        print("\n" + "=" * 80)
        print("✅ Update complete!")
        print("=" * 80)
    else:
        print("\n❌ Failed to fetch NSE data")
