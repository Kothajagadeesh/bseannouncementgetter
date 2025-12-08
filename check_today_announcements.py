#!/usr/bin/env python3
"""Check which companies announced today"""

import requests
from datetime import datetime, timedelta
import json

session = requests.Session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.bseindia.com/corporates/Corpfiling_new.aspx',
}

api_url = 'https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w'

from_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
to_date = datetime.now().strftime('%Y%m%d')

params = {
    'strCat': '-1',
    'strPrevDate': from_date,
    'strScrip': '',
    'strSearch': 'P',
    'strToDate': to_date,
    'strType': 'C'
}

response = session.get(api_url, params=params, headers=headers, timeout=15)

if response.status_code == 200:
    data = response.json()
    
    if 'Table' in data:
        announcements = data['Table']
        print(f"\n{'='*80}")
        print(f"TODAY'S ANNOUNCEMENTS ({len(announcements)} total)")
        print(f"{'='*80}\n")
        
        # Load F&O stocks
        with open('fo_stocks.json', 'r') as f:
            fo_data = json.load(f)
            fo_bse_codes = {stock['bse_code'] for stock in fo_data['stocks']}
        
        fo_count = 0
        non_fo_count = 0
        
        for i, item in enumerate(announcements[:20], 1):  # Show first 20
            bse_code = str(item.get('SCRIP_CD', 'N/A'))
            news_sub = item.get('NEWSSUB', '')
            
            # Extract company name
            company_name = 'N/A'
            if news_sub and ' - ' in news_sub:
                parts = news_sub.split(' - ')
                if len(parts) >= 2:
                    company_name = parts[0].strip()
            
            is_fo = bse_code in fo_bse_codes
            
            if is_fo:
                fo_count += 1
                marker = "✅ F&O"
            else:
                non_fo_count += 1
                marker = "❌ Non-F&O"
            
            print(f"{i:2}. {marker} | {bse_code:8} | {company_name[:50]}")
        
        if len(announcements) > 20:
            print(f"\n... and {len(announcements) - 20} more announcements")
        
        print(f"\n{'='*80}")
        print(f"Summary: {fo_count} F&O eligible, {non_fo_count} non-F&O companies (showing first 20)")
        print(f"{'='*80}\n")
