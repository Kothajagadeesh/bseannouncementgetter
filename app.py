from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import io
import json
import os
import PyPDF2
from urllib.parse import urljoin
from selenium import webdriver
from market_cap_data import get_market_cap_with_cache
import nse_indices
from integrations import slack_integration, telegram_integration, upstox_integration
from integrations.slack_integration import send_to_slack
from integrations.telegram_integration import send_to_telegram
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import hashlib
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))

# Third-party integrations are now in integrations module

# Cache for announcements
announcements_cache = []
last_refresh_time = None  # Track when data was last refreshed

# Track sent announcements to avoid duplicates (stores BSE code + timestamp hash)
sent_announcements = set()

# Background scheduler for auto-refresh
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.start()

# Load F&O eligible stocks
fo_stocks_data = None
fo_bse_codes = set()
fo_nse_symbols = set()

# NSE Indices data
nse_indices_data = {}
nse_symbol_lookup = {}  # Maps NSE symbol to list of indices it belongs to
bse_to_nse_mapping = {}  # Maps BSE code to NSE symbol

def load_fo_stocks():
    """Load F&O eligible stocks from JSON file (NSE-based)"""
    global fo_stocks_data, fo_bse_codes, fo_nse_symbols, bse_to_nse_mapping
    
    try:
        with open('resources/fo_stocks.json', 'r') as f:
            fo_stocks_data = json.load(f)
            
        # Create sets for fast lookup and BSE to NSE mapping
        for stock in fo_stocks_data['stocks']:
            nse_symbol = stock.get('nse_symbol', '')
            bse_code = stock.get('bse_code', '')
            
            # Add NSE symbol (always present in new format)
            if nse_symbol:
                fo_nse_symbols.add(nse_symbol)
            
            # Add BSE code only if present
            if bse_code:
                fo_bse_codes.add(bse_code)
                bse_to_nse_mapping[bse_code] = nse_symbol
        
        print(f"✅ Loaded {len(fo_nse_symbols)} F&O eligible stocks (NSE symbols)")
        if fo_bse_codes:
            print(f"   📄 {len(fo_bse_codes)} stocks have BSE codes mapped")
        return True
    except Exception as e:
        print(f"❌ Error loading F&O stocks: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def is_fo_eligible(bse_code):
    """Check if a stock is F&O eligible"""
    return str(bse_code) in fo_bse_codes

def load_nse_indices():
    """Load NSE indices (Nifty 50, Nifty Next 50, Nifty 500)"""
    global nse_indices_data, nse_symbol_lookup
    
    try:
        print("\n📊 Loading NSE Indices...")
        nse_indices_data = nse_indices.get_all_indices()
        nse_symbol_lookup = nse_indices.create_symbol_lookup()
        
        # Count stocks in each index
        counts = {}
        for index_name, data in nse_indices_data.items():
            if data:
                counts[index_name] = data['count']
        
        print(f"✅ Loaded NSE Indices:")
        print(f"   - Nifty 50: {counts.get('nifty50', 0)} stocks")
        print(f"   - Nifty Next 50: {counts.get('niftynext50', 0)} stocks")
        print(f"   - Nifty 500: {counts.get('nifty500', 0)} stocks")
        print(f"   - Total unique symbols: {len(nse_symbol_lookup)}")
        return True
    except Exception as e:
        print(f"❌ Error loading NSE indices: {str(e)}")
        return False

def get_stock_indices(nse_symbol):
    """Get list of indices a stock belongs to"""
    if not nse_symbol:
        return []
    return nse_symbol_lookup.get(nse_symbol.upper(), [])

def get_nse_symbol_from_bse(bse_code):
    """Get NSE symbol from BSE code"""
    return bse_to_nse_mapping.get(str(bse_code), None)

def download_pdf_locally(pdf_url, company_name, bse_code):
    """Download PDF from BSE and save locally (only if not already exists)"""
    if not pdf_url:
        return None
    
    try:
        # Generate unique identifier using hash of URL
        url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
        
        # Create directory structure: announcements_pdfs/YYYYMMDD/
        date_folder = datetime.now().strftime('%Y%m%d')
        folder_path = os.path.join('announcements_pdfs', date_folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Check if PDF already exists (search by BSE code and hash)
        # This prevents re-downloading the same PDF
        existing_files = [f for f in os.listdir(folder_path) 
                         if f.startswith(f"{bse_code}_") and url_hash in f and f.endswith('.pdf')]
        
        if existing_files:
            existing_path = os.path.join(folder_path, existing_files[0])
            print(f"   ✅ PDF already downloaded: {existing_files[0]}")
            return existing_path
        
        # Create new filename only if not exists
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company_name)[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{bse_code}_{safe_company}_{timestamp}_{url_hash}.pdf"
        file_path = os.path.join(folder_path, filename)
        
        # Download PDF
        headers = get_browser_headers()
        response = requests.get(pdf_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save PDF
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size_kb = len(response.content) / 1024
        print(f"   ✅ Downloaded: {filename} ({file_size_kb:.1f} KB)")
        
        return file_path
        
    except Exception as e:
        print(f"   ❌ Error downloading PDF: {str(e)}")
        return None

# Load F&O stocks on startup
load_fo_stocks()

# Load NSE indices on startup
load_nse_indices()

def create_announcement_id(ann):
    """Create unique ID for announcement to track if already sent"""
    return f"{ann['bse_code']}_{ann['raw_timestamp']}"

def is_nifty_index_stock(ann):
    """Check if announcement is from a Nifty 50, Next 50, or 500 stock"""
    if not ann.get('nse_indices'):
        return False
    indices = ann['nse_indices']
    return 'NIFTY50' in indices or 'NIFTYNEXT50' in indices or 'NIFTY500' in indices

def auto_check_and_notify():
    """Auto-check for new announcements and send Nifty index stocks to Slack"""
    global announcements_cache, sent_announcements, last_refresh_time
    
    try:
        print("\n" + "="*80)
        print(f"🔄 AUTO-CHECK: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("="*80)
        
        # Fetch latest announcements
        new_announcements = fetch_bse_announcements(days_back=1, max_results=200)
        
        if not new_announcements:
            print("⚠️ No announcements fetched")
            return
        
        # Check for new Nifty index announcements
        new_count = 0
        processed_count = 0
        
        for ann in new_announcements:
            ann_id = create_announcement_id(ann)
            
            # Skip if already sent
            if ann_id in sent_announcements:
                continue
            
            new_count += 1
            
            # Check if it's a Nifty index stock
            if is_nifty_index_stock(ann):
                indices_str = ', '.join(ann.get('nse_indices', []))
                print(f"\n📊 NEW Index Stock: {ann['company_name']} ({ann['bse_code']})")
                print(f"   Indices: {indices_str}")
                print(f"   NSE Symbol: {ann.get('nse_symbol', 'N/A')}")
                
                # Auto-summarize and send to Slack
                if ann.get('pdf_link'):
                    print(f"   🤖 Auto-summarizing...")
                    
                    # Download PDF
                    local_pdf = download_pdf_locally(
                        ann['pdf_link'],
                        ann['company_name'],
                        ann['bse_code']
                    )
                    
                    if local_pdf:
                        # Extract text from PDF
                        text = extract_text_from_pdf(local_pdf)
                        
                        if text:
                            # Analyze announcement
                            result = analyze_announcement(text, ann['company_name'])
                            
                            if result:
                                # Send to Slack
                                success = send_to_slack(
                                    ann['company_name'],
                                    ann['bse_code'],
                                    result['sentiment'],
                                    result['summary'],
                                    ann['pdf_link'],
                                    ann.get('date_time', 'N/A')
                                )
                                
                                if success:
                                    # Mark as sent
                                    sent_announcements.add(ann_id)
                                    processed_count += 1
                                    print(f"   ✅ Sent to Slack successfully")
                                else:
                                    print(f"   ❌ Failed to send to Slack")
                            else:
                                print(f"   ⚠️ Analysis failed")
                        else:
                            print(f"   ⚠️ Could not extract PDF text")
                    else:
                        print(f"   ⚠️ Could not download PDF")
                else:
                    print(f"   ⚠️ No PDF link available")
            else:
                # Non-index stock - just mark as seen, don't send
                sent_announcements.add(ann_id)
        
        print(f"\n📈 Auto-check summary:")
        print(f"   - Total announcements: {len(new_announcements)}")
        print(f"   - New announcements: {new_count}")
        print(f"   - Processed & sent: {processed_count}")
        print("="*80 + "\n")
        
        # Update cache
        announcements_cache = new_announcements
        last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        print(f"❌ Error in auto-check: {str(e)}")
        import traceback
        traceback.print_exc()

def get_browser_headers():
    """Returns headers to mimic a real browser"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def fetch_bse_live_api(days_back=1, max_results=200):
    """Fetch live announcements from BSE India API - ACTUAL REAL DATA
    
    Args:
        days_back: Number of days to look back for announcements (default: 1 - today only)
        max_results: Maximum number of announcements to return (default: 200)
    """
    try:
        session = requests.Session()
        
        # Step 1: Get the main page first to establish session
        main_url = 'https://www.bseindia.com/corporates/Corpfiling_new.aspx'
        headers = get_browser_headers()
        headers.update({
            'Referer': 'https://www.bseindia.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        response = session.get(main_url, headers=headers, timeout=15)
        print(f"BSE main page status: {response.status_code}")
        
        # Step 2: Call the announcements data endpoint  
        # This URL returns JSON data for latest corporate filings
        api_url = 'https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w'
        
        # Get date range in YYYYMMDD format
        # For days_back=1 (default), fetch only today's announcements
        to_date = datetime.now().strftime('%Y%m%d')
        if days_back <= 1:
            from_date = to_date  # Only today
        else:
            from_date = (datetime.now() - timedelta(days=days_back-1)).strftime('%Y%m%d')
        
        print(f"Fetching announcements from {from_date} to {to_date} (Today only)" if from_date == to_date else f"Fetching announcements from {from_date} to {to_date}")
        
        params = {
            'strCat': '-1',  # All categories
            'strPrevDate': from_date,  # Start date
            'strScrip': '',  # All scrips
            'strSearch': 'P',  # Search type
            'strToDate': to_date,  # End date
            'strType': 'C'  # Corporate announcements
        }
        
        api_headers = {
            'User-Agent': headers['User-Agent'],
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.bseindia.com/corporates/Corpfiling_new.aspx',
            'Origin': 'https://www.bseindia.com',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        print(f"Fetching BSE API: {api_url}")
        api_response = session.get(api_url, params=params, headers=api_headers, timeout=15)
        
        print(f"BSE API status: {api_response.status_code}")
        print(f"Content-Type: {api_response.headers.get('Content-Type')}")
        
        if api_response.status_code == 200:
            try:
                data = api_response.json()
                
                if isinstance(data, dict) and 'Table' in data:
                    announcements = []
                    table_data = data['Table']
                    total_available = len(table_data)
                    
                    print(f"\n✅ BSE API SUCCESS! Found {total_available} announcements")
                    print("Processing all announcements...")
                    
                    for item in table_data[:max_results]:
                        # Extract data from API response
                        # NEWSSUB contains the full announcement text with company name and code
                        news_sub = item.get('NEWSSUB', '')
                        bse_code = str(item.get('SCRIP_CD', 'N/A'))
                        
                        # ATTACHMENTNAME contains the actual PDF filename!
                        attachment_name = item.get('ATTACHMENTNAME', '')
                        
                        # Extract date/time when announcement was published
                        # NEWS_DT format: 2025-12-02T22:36:41.373
                        news_date = item.get('NEWS_DT', item.get('DT_TM', ''))
                        
                        # Format the date/time nicely and keep raw timestamp
                        formatted_date = ''
                        raw_timestamp = ''
                        if news_date:
                            try:
                                # Parse ISO format datetime
                                dt = datetime.fromisoformat(news_date.replace('T', ' ').split('.')[0])
                                # Format as: Dec 02, 2025 10:36 PM
                                formatted_date = dt.strftime('%b %d, %Y %I:%M %p')
                                # Keep ISO format for JavaScript processing
                                raw_timestamp = dt.isoformat()
                            except:
                                formatted_date = news_date
                                raw_timestamp = news_date
                        
                        # Extract company name from NEWSSUB (format: "Company Name - CODE - Details...")
                        company_name = 'N/A'
                        if news_sub and ' - ' in news_sub:
                            parts = news_sub.split(' - ')
                            if len(parts) >= 2:
                                company_name = parts[0].strip()
                        
                        # Construct PDF link using ATTACHMENTNAME (the ACTUAL PDF filename)
                        pdf_link = ''
                        if attachment_name:
                            # ATTACHMENTNAME already includes .pdf extension
                            pdf_link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attachment_name}"
                        
                        # Check if stock is F&O eligible (for display purposes only)
                        is_fo = is_fo_eligible(bse_code)
                        
                        # Get NSE symbol and indices information
                        nse_symbol = get_nse_symbol_from_bse(bse_code)
                        stock_indices = get_stock_indices(nse_symbol) if nse_symbol else []
                        
                        # Get market cap category
                        market_cap_info = get_market_cap_with_cache(bse_code) if is_fo else {
                            'category': 'Unknown',
                            'emoji': '⚪',
                            'color': '#6b7280'
                        }
                        
                        # Don't download PDF here - will download on-demand when user clicks Summarize
                        # Check if PDF already exists locally from previous downloads
                        url_hash = hashlib.md5(pdf_link.encode()).hexdigest()[:8] if pdf_link else None
                        local_pdf_path = None
                        
                        if url_hash:
                            date_folder = datetime.now().strftime('%Y%m%d')
                            folder_path = os.path.join('announcements_pdfs', date_folder)
                            if os.path.exists(folder_path):
                                existing_files = [f for f in os.listdir(folder_path) 
                                                if f.startswith(f"{bse_code}_") and url_hash in f and f.endswith('.pdf')]
                                if existing_files:
                                    local_pdf_path = os.path.join(folder_path, existing_files[0])
                        
                        announcements.append({
                            'company_name': company_name,
                            'bse_code': bse_code,
                            'nse_symbol': nse_symbol,
                            'nse_indices': stock_indices,
                            'pdf_link': pdf_link,  # BSE link (primary)
                            'local_pdf_path': local_pdf_path,  # Local file path (if exists from previous download)
                            'date_time': formatted_date,
                            'raw_timestamp': raw_timestamp,
                            'market_cap': market_cap_info,
                            'is_fo_eligible': is_fo,
                            'summary': None
                        })
                    
                    print(f"✅ Processed {len(announcements)} announcements")
                    return announcements
                else:
                    print(f"Unexpected data structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Response content (first 500 chars): {api_response.text[:500]}")
                return []
        else:
            print(f"API returned status {api_response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching BSE live API: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def fetch_nse_announcements():
    """Fetch announcements from NSE India as alternative source"""
    try:
        # NSE announcements API endpoint
        url = "https://www.nseindia.com/api/corporate-announcements"
        
        headers = get_browser_headers()
        headers['Accept'] = 'application/json'
        
        session = requests.Session()
        
        # First, visit the main page to get cookies
        session.get('https://www.nseindia.com', headers=headers, timeout=10)
        time.sleep(2)
        
        # Now fetch announcements
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        announcements = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'data' in data:
            items = data['data']
        else:
            items = []
        
        for item in items[:50]:
            announcements.append({
                'company_name': item.get('symbol', '') + ' - ' + item.get('sm_name', item.get('companyName', 'N/A')),
                'bse_code': item.get('symbol', 'N/A'),
                'pdf_link': item.get('attachment', item.get('an_dt', '')),
                'summary': None
            })
        
        return announcements
        
    except Exception as e:
        print(f"Error fetching NSE announcements: {str(e)}")
        return []

def get_sample_announcements():
    """Return sample announcements for demonstration"""
    # Get current time for sample data
    now = datetime.now()
    current_time = now.strftime('%b %d, %Y %I:%M %p')
    current_timestamp = now.isoformat()
    
    return [
        {
            'company_name': 'Reliance Industries Limited',
            'bse_code': '500325',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/c4c8c8e5-5b5a-4f0e-9f3f-7e8e8e8e8e8e.pdf',
            'local_pdf_path': None,
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'market_cap': {'category': 'Large Cap', 'emoji': '🟢', 'color': '#10b981'},
            'summary': None
        },
        {
            'company_name': 'Tata Consultancy Services Ltd',
            'bse_code': '532540',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/a1b2c3d4-5678-90ab-cdef-1234567890ab.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'HDFC Bank Limited',
            'bse_code': '500180',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/d4c3b2a1-8765-09ba-fedc-0987654321ba.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'Infosys Limited',
            'bse_code': '500209',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/e5f6g7h8-1234-5678-9abc-def123456789.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'ICICI Bank Limited',
            'bse_code': '532174',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/f6g7h8i9-2345-6789-0abc-def234567890.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'State Bank of India',
            'bse_code': '500112',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/g7h8i9j0-3456-7890-1abc-def345678901.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'Bharti Airtel Limited',
            'bse_code': '532454',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/h8i9j0k1-4567-8901-2abc-def456789012.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'ITC Limited',
            'bse_code': '500875',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/i9j0k1l2-5678-9012-3abc-def567890123.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'Larsen & Toubro Limited',
            'bse_code': '500510',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/j0k1l2m3-6789-0123-4abc-def678901234.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        },
        {
            'company_name': 'Hindustan Unilever Limited',
            'bse_code': '500696',
            'pdf_link': 'https://www.bseindia.com/xml-data/corpfiling/AttachLive/k1l2m3n4-7890-1234-5abc-def789012345.pdf',
            'date_time': current_time,
            'raw_timestamp': current_timestamp,
            'summary': None
        }
    ]

def fetch_bse_announcements(days_back=1, max_results=200):
    """Fetch announcements from BSE - LIVE DATA
    
    Args:
        days_back: Number of days to look back (default: 1 - today only)
        max_results: Maximum number of results (default: 200)
    """
    print("\n" + "="*80)
    print(f"FETCHING LIVE BSE ANNOUNCEMENTS (Last {days_back} days, max {max_results} results)...")
    print("="*80)
    
    # Fetch from BSE Live API (REAL DATA)
    announcements = fetch_bse_live_api(days_back=days_back, max_results=max_results)
    
    if announcements:
        print(f"✅ SUCCESS! Fetched {len(announcements)} LIVE announcements from BSE India")
        print("="*80 + "\n")
        return announcements
    
    print("❌ BSE API failed, using sample data for demonstration")
    print("="*80 + "\n")
    
    # Return sample data as last resort
    return get_sample_announcements()

def extract_text_from_pdf(pdf_source):
    """Extract text from PDF (supports both local file path and URL)"""
    try:
        # Check if it's a local file path
        if os.path.exists(pdf_source):
            # Read from local file
            with open(pdf_source, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages[:5]:  # Read first 5 pages only
                    text += page.extract_text()
                return text[:5000]  # Limit to 5000 characters
        else:
            # Download from URL
            response = requests.get(pdf_source, headers=get_browser_headers(), timeout=30)
            response.raise_for_status()
            
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages[:5]:  # Read first 5 pages only
                text += page.extract_text()
            
            return text[:5000]  # Limit to 5000 characters
        
    except Exception as e:
        print(f"Error extracting PDF: {str(e)}")
        return ""

def analyze_with_python(text, company_name):
    """Python-based keyword analysis (fallback when OpenAI is not available)"""
    # Simple keyword-based analysis
    positive_keywords = ['growth', 'profit', 'increase', 'expansion', 'dividend', 'acquisition', 
                         'revenue', 'gain', 'success', 'partnership', 'award', 'milestone',
                         'improved', 'strong', 'positive', 'progress', 'buyback']
    
    negative_keywords = ['loss', 'decline', 'decrease', 'bankruptcy', 'lawsuit', 'penalty',
                        'investigation', 'fraud', 'default', 'resignation', 'closure',
                        'weak', 'negative', 'downgrade', 'risk']
    
    text_lower = text.lower()
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
    
    # Determine sentiment
    if positive_count > negative_count:
        sentiment = 'positive'
        sentiment_text = '📈 POSITIVE'
    elif negative_count > positive_count:
        sentiment = 'negative'
        sentiment_text = '📉 NEGATIVE'
    else:
        sentiment = 'neutral'
        sentiment_text = '➖ NEUTRAL'
    
    # Generate summary
    sentences = re.split(r'[.!?]\s+', text)
    important_sentences = []
    
    for sentence in sentences[:20]:  # Check first 20 sentences
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in positive_keywords + negative_keywords):
            if len(sentence.split()) > 5:  # Ensure sentence has substance
                important_sentences.append(sentence.strip())
                if len(important_sentences) >= 3:
                    break
    
    if not important_sentences:
        important_sentences = sentences[:3]
    
    summary_lines = [
        f"{sentiment_text}",
        f"Company: {company_name}",
        f"Analysis: Python-based keyword matching",
        *important_sentences[:2]
    ]
    
    return {
        'summary': '\n'.join(summary_lines),
        'sentiment': sentiment
    }

def analyze_announcement(text, company_name):
    """Analyze announcement using OpenAI GPT-3.5-turbo with Python fallback"""
    if not text:
        return {
            'summary': f"Unable to extract content from the announcement PDF for {company_name}.",
            'sentiment': 'neutral'
        }
    
    # Check if OpenAI API key is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️ OPENAI_API_KEY not set, using Python-based analysis")
        return analyze_with_python(text, company_name)
    
    try:
        
        # Truncate text to avoid token limits (GPT-3.5-turbo has 4096 token limit)
        max_chars = 12000  # Roughly 3000 tokens
        truncated_text = text[:max_chars]
        
        print(f"🤖 Sending to OpenAI gpt-4o-mini for analysis...")
        print(f"   Text length: {len(truncated_text)} characters")
        
        # Call OpenAI API with the user's specific prompt
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert stock market analyst. Read the PDF content and suggest Positive, Negative or Neutral. Don't provide any explanation."
                },
                {
                    "role": "user",
                    "content": f"Company: {company_name}\n\nAnnouncement Content:\n{truncated_text}"
                }
            ],
            temperature=0.3,
            max_tokens=10  # We only need one word: Positive/Negative/Neutral
        )
        
        # Extract the sentiment from OpenAI response
        ai_response = response.choices[0].message.content.strip()
        print(f"✅ OpenAI Response: {ai_response}")
        
        # Normalize the response
        ai_response_lower = ai_response.lower()
        if 'positive' in ai_response_lower:
            sentiment = 'positive'
            sentiment_text = '📈 POSITIVE'
        elif 'negative' in ai_response_lower:
            sentiment = 'negative'
            sentiment_text = '📉 NEGATIVE'
        else:
            sentiment = 'neutral'
            sentiment_text = '➖ NEUTRAL'
        
        return {
            'summary': f"{sentiment_text}\nCompany: {company_name}\nAnalysis: {ai_response}",
            'sentiment': sentiment
        }
        
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {str(e)}")
        print("⚠️ Falling back to Python-based analysis")
        return analyze_with_python(text, company_name)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/pdf/<path:filepath>')
def serve_pdf(filepath):
    """Serve local PDF files"""
    try:
        # Security: ensure the path is within announcements_pdfs folder
        safe_path = os.path.join('announcements_pdfs', filepath)
        
        if not os.path.exists(safe_path):
            return jsonify({'error': 'PDF not found'}), 404
        
        # Serve the PDF file
        return send_file(safe_path, mimetype='application/pdf')
        
    except Exception as e:
        print(f"Error serving PDF: {str(e)}")
        return jsonify({'error': 'Error loading PDF'}), 500

@app.route('/fando-club')
def fando_club():
    """Render the F&O Club calculator page"""
    return render_template('fando-club.html')

@app.route('/api/options-advisor', methods=['POST'])
def options_advisor():
    """AI-powered options trading advisor"""
    try:
        data = request.json
        capital = data.get('capital', 100000)
        expected_return = data.get('expected_return', 2)  # percentage
        risk_level = data.get('risk_level', 'moderate')
        
        target_amount = (capital * expected_return) / 100
        
        print(f"\n🤖 AI Options Advisor Request:")
        print(f"   Capital: ₹{capital:,}")
        print(f"   Expected Return: {expected_return}% (₹{target_amount:,})")
        print(f"   Risk Level: {risk_level}")
        
        # Check Upstox authentication
        if not upstox_integration.is_authenticated():
            return jsonify({
                'success': False,
                'error': 'Upstox not authenticated. Please login first.',
                'redirect': '/upstox/login'
            }), 401
        
        # Fetch options data for ALL F&O stocks
        print(f"\n📊 Fetching options data...")
        options_data = upstox_integration.upstox_client.get_all_fo_options_summary()
        
        if isinstance(options_data, dict) and options_data.get('error'):
            return jsonify({
                'success': False,
                'error': options_data['error']
            }), 500
        
        # Prepare context for OpenAI
        prompt = f"""
You are a well-planned trader in Indian markets (BSE & NSE). You consider all possible news, market conditions, and technical analysis.

Client Requirements:
- Capital Available: ₹{capital:,}
- Target Monthly Return: {expected_return}% (₹{target_amount:,})
- Risk Tolerance: {risk_level.upper()}

Options Data Available:
{json.dumps(options_data, indent=2)[:3000]}...

Based on the current market data and options available, provide your top 3-5 trading recommendations.

For each recommendation, specify:
1. Stock Symbol
2. Option Type (CE/PE)
3. Action (BUY/SELL)
4. Strike Price
5. Expiry Date
6. Lot Size
7. Expected Premium
8. Expected Profit
9. Risk Assessment
10. Reasoning

Format your response as a clear, actionable strategy that a trader can execute immediately.
"""
        
        # Call OpenAI for analysis
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not configured'
            }), 500
        
        print(f"\n🧠 Sending to OpenAI for analysis...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert options trader with deep knowledge of Indian stock markets."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_recommendations = response.choices[0].message.content
        print(f"\n✅ AI Analysis Complete")
        
        return jsonify({
            'success': True,
            'capital': capital,
            'target_return': target_amount,
            'risk_level': risk_level,
            'recommendations': ai_recommendations,
            'options_data_summary': {
                'symbols_analyzed': len(options_data),
                'symbols': list(options_data.keys()) if isinstance(options_data, dict) else []
            }
        })
        
    except Exception as e:
        print(f"❌ Error in options advisor: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/options-chain')
def options_chain_viewer():
    """Options Chain Viewer UI"""
    return render_template('options-chain.html')

@app.route('/api/options-chain/<symbol>')
def api_options_chain(symbol):
    """API endpoint to fetch options chain with live data"""
    try:
        from datetime import datetime
        import gzip
        import urllib.request
        
        print(f"\n📊 Fetching options chain for {symbol}...")
        
        # Download Upstox instruments data
        url = 'https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz'
        response = urllib.request.urlopen(url)
        compressed_data = response.read()
        decompressed_data = gzip.decompress(compressed_data)
        all_instruments = json.loads(decompressed_data)
        
        # Find all options for this symbol
        symbol_options = [
            item for item in all_instruments
            if symbol.upper() in item.get('trading_symbol', '')
            and item.get('instrument_type') in ['CE', 'PE']
            and item.get('segment') == 'NSE_FO'
        ]
        
        print(f"🔍 Found {len(symbol_options)} total options for {symbol}")
        
        # Filter out expired options
        today = datetime.now()
        filtered_options = []
        
        for option in symbol_options:
            expiry_timestamp = option.get('expiry')
            if expiry_timestamp:
                # Convert milliseconds to datetime
                expiry_date = datetime.fromtimestamp(expiry_timestamp / 1000)
                
                # Only include if expiry is today or future
                if expiry_date.date() >= today.date():
                    filtered_options.append(option)
        
        print(f"✅ Found {len(filtered_options)} active options (filtered {len(symbol_options) - len(filtered_options)} expired)")
        
        # Fetch underlying stock price
        stock_price_data = None
        if upstox_integration.is_authenticated():
            print(f"📊 Fetching underlying stock price for {symbol}...")
            stock_quotes = upstox_integration.upstox_client.get_market_quotes_multiple([symbol])
            if stock_quotes and not stock_quotes.get('error'):
                stock_data_dict = stock_quotes.get('data', {})
                if stock_data_dict:
                    # Get first (and only) stock data
                    stock_price_data = list(stock_data_dict.values())[0] if stock_data_dict else None
                    if stock_price_data:
                        print(f"✅ Stock LTP: ₹{stock_price_data.get('last_price', 0)}")
        
        # Fetch live market data for options (in batches)
        if upstox_integration.is_authenticated() and filtered_options:
            print(f"📈 Fetching live market data...")
            
            # Batch fetch market quotes (max 500 at a time)
            batch_size = 500
            for i in range(0, len(filtered_options), batch_size):
                batch = filtered_options[i:i+batch_size]
                instrument_keys = [opt['instrument_key'] for opt in batch]
                
                # Fetch market data using instrument keys directly
                market_data = upstox_integration.upstox_client.get_quotes_by_instrument_keys(instrument_keys)
                
                if market_data and not market_data.get('error'):
                    # Merge live data into options
                    data_dict = market_data.get('data', {})
                    
                    # Build mapping from instrument_token to quote data
                    # Response keys are like 'NSE_FO:TCS25DEC2600CE' but contain 'instrument_token' field
                    token_to_quote = {}
                    for resp_key, resp_value in data_dict.items():
                        if isinstance(resp_value, dict) and 'instrument_token' in resp_value:
                            token_to_quote[resp_value['instrument_token']] = resp_value
                    
                    # Map live data back to options
                    for option in batch:
                        option_key = option['instrument_key']
                        if option_key in token_to_quote:
                            quote = token_to_quote[option_key]
                            option['last_price'] = quote.get('last_price', 0)
                            option['volume'] = quote.get('volume', 0)
                            option['oi'] = quote.get('oi', 0)
                            option['ohlc'] = quote.get('ohlc', {})
            
            print(f"✅ Fetched live data for {len(filtered_options)} options")
        else:
            print(f"⚠️ Skipping live data (not authenticated or no options)")
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'total_options': len(filtered_options),
            'stock_price': stock_price_data,
            'data': filtered_options
        })
        
    except Exception as e:
        print(f"❌ Error fetching options chain: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fo-symbols')
def api_fo_symbols():
    """Get list of all F&O symbols for autocomplete"""
    try:
        symbols = sorted(list(fo_nse_symbols))
        return jsonify({
            'success': True,
            'symbols': symbols,
            'total': len(symbols)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/bse-instruments')
def bse_instruments():
    """Display BSE instruments browser"""
    return render_template('bse-instruments.html')

@app.route('/api/bse-instruments')
def api_bse_instruments():
    """API endpoint to fetch BSE instruments data"""
    try:
        import gzip
        import urllib.request
        
        # Download and parse Upstox instruments data
        url = 'https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz'
        
        print(f"\n📥 Downloading Upstox instruments data...")
        response = urllib.request.urlopen(url)
        compressed_data = response.read()
        
        print(f"📦 Decompressing data...")
        decompressed_data = gzip.decompress(compressed_data)
        all_instruments = json.loads(decompressed_data)
        
        print(f"🔍 Filtering BSE instruments...")
        bse_instruments = [
            item for item in all_instruments 
            if item.get('exchange') == 'BSE'
        ]
        
        print(f"✅ Found {len(bse_instruments)} BSE instruments")
        
        return jsonify({
            'success': True,
            'total': len(bse_instruments),
            'data': bse_instruments
        })
    except Exception as e:
        print(f"❌ Error fetching BSE instruments: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upstox/login')
def upstox_login():
    """Initiate Upstox OAuth flow"""
    redirect_uri = request.url_root + 'upstox/callback'
    if not upstox_integration.upstox_client.api_key:
        return jsonify({
            'error': 'Upstox API Key not configured',
            'message': 'Please set UPSTOX_API_KEY and UPSTOX_API_SECRET environment variables'
        }), 500
    
    auth_url = upstox_integration.upstox_client.get_authorization_url(redirect_uri)
    return redirect(auth_url)

@app.route('/upstox/callback')
def upstox_callback():
    """Handle Upstox OAuth callback"""
    auth_code = request.args.get('code')
    
    if not auth_code:
        return jsonify({'error': 'No authorization code received'}), 400
    
    redirect_uri = request.url_root + 'upstox/callback'
    token_data = upstox_integration.upstox_client.get_access_token(auth_code, redirect_uri)
    
    if token_data and token_data.get('access_token'):
        # Store access token in session
        session['upstox_access_token'] = token_data['access_token']
        
        # Also update environment variable for persistence
        os.environ['UPSTOX_ACCESS_TOKEN'] = token_data['access_token']
        
        print(f"✅ Upstox authenticated successfully!")
        print(f"   Access Token: {token_data['access_token'][:20]}...")
        
        return redirect('/upstox/live-data')
    else:
        return jsonify({'error': 'Failed to get access token', 'details': token_data}), 500

@app.route('/upstox/live-data')
def upstox_live_data_page():
    """Render Upstox live data dashboard"""
    is_auth = upstox_integration.is_authenticated()
    return render_template('upstox-live.html', is_authenticated=is_auth)

@app.route('/api/upstox/status')
def upstox_status():
    """Check Upstox authentication status"""
    is_auth = upstox_integration.is_authenticated()
    
    status_data = {
        'authenticated': is_auth,
        'api_key_set': bool(upstox_integration.upstox_client.api_key)
    }
    
    if is_auth:
        # Try to fetch user profile
        profile = upstox_integration.upstox_client.get_user_profile()
        if not profile.get('error'):
            status_data['user'] = profile.get('data', {})
    
    return jsonify(status_data)

@app.route('/api/upstox/quote/<symbol>')
def upstox_get_quote(symbol):
    """Get live market quote for a symbol"""
    if not upstox_integration.is_authenticated():
        return jsonify({'error': 'Not authenticated. Please login first.'}), 401
    
    quote = upstox_integration.upstox_client.get_market_quote(symbol)
    return jsonify(quote)

@app.route('/api/upstox/quotes')
def upstox_get_quotes():
    """Get live market quotes for multiple symbols"""
    if not upstox_integration.is_authenticated():
        return jsonify({'error': 'Not authenticated. Please login first.'}), 401
    
    symbols = request.args.get('symbols', '').split(',')
    if not symbols or not symbols[0]:
        return jsonify({'error': 'No symbols provided'}), 400
    
    quotes = upstox_integration.upstox_client.get_market_quotes_multiple(symbols)
    return jsonify(quotes)

@app.route('/api/nse-indices')
def get_nse_indices_api():
    """API endpoint to get NSE indices data"""
    return jsonify({
        'success': True,
        'data': nse_indices_data,
        'symbol_count': len(nse_symbol_lookup)
    })

@app.route('/api/nse-indices/<index_name>')
def get_specific_index(index_name):
    """API endpoint to get a specific NSE index"""
    index_name_lower = index_name.lower()
    
    if index_name_lower not in nse_indices_data:
        return jsonify({'success': False, 'error': 'Index not found'}), 404
    
    return jsonify({
        'success': True,
        'data': nse_indices_data[index_name_lower]
    })

@app.route('/api/check-symbol/<symbol>')
def check_symbol_indices(symbol):
    """API endpoint to check which indices a symbol belongs to"""
    indices = get_stock_indices(symbol)
    
    return jsonify({
        'success': True,
        'symbol': symbol.upper(),
        'indices': indices,
        'count': len(indices)
    })

@app.route('/api/announcements')
def get_announcements():
    """API endpoint to get announcements"""
    global announcements_cache, last_refresh_time
    
    # Get days_back parameter from query string (default: 1 day - today only)
    days_back = request.args.get('days_back', default=1, type=int)
    max_results = request.args.get('max_results', default=200, type=int)
    
    # Validate parameters
    days_back = min(max(1, days_back), 30)  # Between 1 and 30 days
    max_results = min(max(10, max_results), 500)  # Between 10 and 500 results
    
    print(f"API Request: days_back={days_back}, max_results={max_results}")
    
    # Fetch fresh data
    announcements_cache = fetch_bse_announcements(days_back=days_back, max_results=max_results)
    
    # Update last refresh time
    last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'success': True,
        'data': announcements_cache,
        'count': len(announcements_cache),
        'days_back': days_back,
        'max_results': max_results,
        'last_refresh': last_refresh_time
    })

# send_to_slack and send_to_telegram are now imported from integrations module

@app.route('/api/summarize', methods=['POST'])
def summarize_announcement():
    """API endpoint to summarize an announcement"""
    data = request.json
    pdf_url = data.get('pdf_link')
    company_name = data.get('company_name')
    bse_code = data.get('bse_code', 'UNKNOWN')
    announcement_time = data.get('date_time', 'N/A')
    
    if not pdf_url or not company_name:
        return jsonify({
            'success': False,
            'error': 'Missing required parameters'
        }), 400
    
    # Download PDF locally (on-demand, only when summarizing)
    print(f"\n📊 Summarize requested for {company_name} ({bse_code})")
    print(f"🔽 Downloading PDF for analysis...")
    local_pdf_path = download_pdf_locally(pdf_url, company_name, bse_code)
    
    # Extract text from PDF (use local if available, otherwise from URL)
    if local_pdf_path and os.path.exists(local_pdf_path):
        print(f"📄 Using local PDF: {os.path.basename(local_pdf_path)}")
        # Read from local file
        with open(local_pdf_path, 'rb') as f:
            pdf_file = io.BytesIO(f.read())
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pdf_text = ""
            for page in pdf_reader.pages[:5]:  # Read first 5 pages
                pdf_text += page.extract_text()
            pdf_text = pdf_text[:5000]  # Limit to 5000 characters
    else:
        print(f"⚠️ Local download failed, extracting from BSE URL...")
        pdf_text = extract_text_from_pdf(pdf_url)
    
    # Analyze and generate summary
    analysis = analyze_announcement(pdf_text, company_name)
    
    # Send to Slack and Telegram
    slack_sent = send_to_slack(
        company_name=company_name,
        bse_code=bse_code,
        sentiment=analysis['sentiment'],
        summary=analysis['summary'],
        pdf_url=pdf_url,
        announcement_time=announcement_time
    )
    
    telegram_sent = send_to_telegram(
        company_name=company_name,
        bse_code=bse_code,
        sentiment=analysis['sentiment'],
        summary=analysis['summary'],
        pdf_url=pdf_url
    )
    
    # Prepare response with delivery status
    delivery_status = []
    if slack_sent:
        delivery_status.append('Slack')
    if telegram_sent:
        delivery_status.append('Telegram')
    
    return jsonify({
        'success': True,
        'summary': analysis['summary'],
        'sentiment': analysis['sentiment'],
        'delivered_to': delivery_status if delivery_status else ['None (configure tokens)']
    })

# Configure auto-refresh scheduler
# Market hours: 9:00 AM - 3:30 PM IST (every 1 minute)
# Non-market hours: 3:31 PM - 8:59 AM IST (every 10 minutes)

# Job 1: Every 1 minute during market hours (9:00 AM - 3:30 PM)
scheduler.add_job(
    auto_check_and_notify,
    CronTrigger(
        hour='9-14',  # 9 AM to 2 PM (every minute)
        minute='*',
        timezone='Asia/Kolkata'
    ),
    id='market_hours_frequent',
    name='Market Hours Check (Every 1 min)'
)

# Job 2: Every 1 minute from 3:00 PM to 3:30 PM
scheduler.add_job(
    auto_check_and_notify,
    CronTrigger(
        hour='15',  # 3 PM
        minute='0-30',  # First 30 minutes
        timezone='Asia/Kolkata'
    ),
    id='market_hours_closing',
    name='Market Closing Hours (Every 1 min)'
)

# Job 3: Every 10 minutes during non-market hours
scheduler.add_job(
    auto_check_and_notify,
    CronTrigger(
        minute='*/10',  # Every 10 minutes
        timezone='Asia/Kolkata'
    ),
    id='non_market_hours',
    name='Non-Market Hours Check (Every 10 min)'
)

print("\n" + "="*80)
print("🔔 AUTO-NOTIFICATION SCHEDULER CONFIGURED")
print("="*80)
print("🟢 Market Hours (9:00 AM - 3:30 PM IST): Check every 1 minute")
print("🟡 Non-Market Hours (3:31 PM - 8:59 AM IST): Check every 10 minutes")
print("🎯 Auto-send to Slack: Nifty 50, Next 50, and 500 stocks only")
print("="*80 + "\n")

# Run initial check
print("🚀 Running initial announcement check...")
auto_check_and_notify()

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Shutdown scheduler on exit
        scheduler.shutdown()
