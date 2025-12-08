#!/usr/bin/env python3
"""Test script to debug BSE and NSE API calls"""

import requests
from datetime import datetime, timedelta
import json

def test_bse_api():
    """Test BSE API call"""
    print("\n" + "="*80)
    print("TESTING BSE API")
    print("="*80)
    
    try:
        session = requests.Session()
        
        # Headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.bseindia.com/corporates/Corpfiling_new.aspx',
            'Origin': 'https://www.bseindia.com',
        }
        
        # API URL
        api_url = 'https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w'
        
        # Date range
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
        
        print(f"Fetching from {from_date} to {to_date}...")
        print(f"URL: {api_url}")
        print(f"Params: {params}")
        
        response = session.get(api_url, params=params, headers=headers, timeout=15)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Length: {len(response.text)} bytes")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ JSON parsed successfully!")
                
                if isinstance(data, dict):
                    print(f"Keys in response: {list(data.keys())}")
                    
                    if 'Table' in data:
                        announcements = data['Table']
                        print(f"Number of announcements: {len(announcements)}")
                        
                        if announcements:
                            print(f"\nFirst announcement:")
                            first = announcements[0]
                            print(f"  - Company: {first.get('NEWSSUB', 'N/A')[:80]}")
                            print(f"  - BSE Code: {first.get('SCRIP_CD', 'N/A')}")
                            print(f"  - Date: {first.get('NEWS_DT', 'N/A')}")
                            print(f"  - PDF: {first.get('ATTACHMENTNAME', 'N/A')}")
                    else:
                        print(f"⚠️ No 'Table' key found in response")
                else:
                    print(f"⚠️ Response is not a dict: {type(data)}")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON decode error: {str(e)}")
                print(f"First 500 chars of response: {response.text[:500]}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_nse_api():
    """Test NSE API call"""
    print("\n" + "="*80)
    print("TESTING NSE API")
    print("="*80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        session = requests.Session()
        
        # First visit the main page to get cookies
        print("Step 1: Getting cookies from main page...")
        main_response = session.get('https://www.nseindia.com', headers=headers, timeout=10)
        print(f"Main page status: {main_response.status_code}")
        print(f"Cookies received: {list(session.cookies.keys())}")
        
        import time
        time.sleep(2)
        
        # Now fetch announcements
        print("\nStep 2: Fetching announcements...")
        url = "https://www.nseindia.com/api/corporate-announcements"
        response = session.get(url, headers=headers, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Length: {len(response.text)} bytes")
        print(f"First 200 chars: {response.text[:200]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ JSON parsed successfully!")
                print(f"Type: {type(data)}")
                
                if isinstance(data, list):
                    print(f"Number of announcements: {len(data)}")
                elif isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON decode error: {str(e)}")
                
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bse_api()
    test_nse_api()
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)
