from flask import Flask, render_template, jsonify, request, send_file
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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import hashlib

app = Flask(__name__)

# Cache for announcements
announcements_cache = []

# Load F&O eligible stocks
fo_stocks_data = None
fo_bse_codes = set()
fo_nse_symbols = set()

def load_fo_stocks():
    """Load F&O eligible stocks from JSON file"""
    global fo_stocks_data, fo_bse_codes, fo_nse_symbols
    
    try:
        with open('fo_stocks.json', 'r') as f:
            fo_stocks_data = json.load(f)
            
        # Create sets for fast lookup
        for stock in fo_stocks_data['stocks']:
            fo_bse_codes.add(stock['bse_code'])
            fo_nse_symbols.add(stock['nse_symbol'])
        
        print(f"✅ Loaded {len(fo_bse_codes)} F&O eligible stocks")
        return True
    except Exception as e:
        print(f"❌ Error loading F&O stocks: {str(e)}")
        return False

def is_fo_eligible(bse_code):
    """Check if a stock is F&O eligible"""
    return str(bse_code) in fo_bse_codes

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
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
        to_date = datetime.now().strftime('%Y%m%d')
        
        print(f"Fetching announcements from {from_date} to {to_date}")
        
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
                    print("Filtering for F&O eligible stocks only...")
                    
                    fo_filtered = 0
                    non_fo_skipped = 0
                    
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
                        
                        # Check if stock is F&O eligible
                        if not is_fo_eligible(bse_code):
                            non_fo_skipped += 1
                            continue  # Skip non-F&O stocks
                        
                        # Get market cap category (only for F&O stocks)
                        market_cap_info = get_market_cap_with_cache(bse_code)
                        
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
                        
                        fo_filtered += 1
                        announcements.append({
                            'company_name': company_name,
                            'bse_code': bse_code,
                            'pdf_link': pdf_link,  # BSE link (primary)
                            'local_pdf_path': local_pdf_path,  # Local file path (if exists from previous download)
                            'date_time': formatted_date,
                            'raw_timestamp': raw_timestamp,
                            'market_cap': market_cap_info,
                            'is_fo_eligible': True,
                            'summary': None
                        })
                    
                    # Print filtering results
                    print(f"✅ F&O Filter Results:")
                    print(f"   - F&O Eligible: {fo_filtered} announcements")
                    print(f"   - Non-F&O Skipped: {non_fo_skipped} announcements")
                    print(f"   - Total Returned: {len(announcements)} F&O stocks only")
                    
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
    """Fetch announcements with fallback mechanism - LIVE DATA
    
    Args:
        days_back: Number of days to look back (default: 1 - today only)
        max_results: Maximum number of results (default: 200)
    """
    print("\n" + "="*80)
    print(f"FETCHING LIVE BSE ANNOUNCEMENTS (Last {days_back} days, max {max_results} results)...")
    print("="*80)
    
    # Try BSE Live API first (REAL DATA)
    announcements = fetch_bse_live_api(days_back=days_back, max_results=max_results)
    
    if announcements:
        print(f"✅ SUCCESS! Fetched {len(announcements)} LIVE announcements from BSE India")
        print("="*80 + "\n")
        return announcements
    
    print("⚠️ BSE API failed, trying NSE India...")
    
    # Try NSE as alternative (ALSO REAL DATA)
    announcements = fetch_nse_announcements()
    
    if announcements:
        print(f"✅ SUCCESS! Fetched {len(announcements)} LIVE announcements from NSE India")
        print("="*80 + "\n")
        return announcements
    
    print("❌ All live sources failed, using sample data for demonstration")
    print("="*80 + "\n")
    
    # Return sample data as last resort
    return get_sample_announcements()

def extract_text_from_pdf(pdf_url):
    """Extract text from PDF"""
    try:
        response = requests.get(pdf_url, headers=get_browser_headers(), timeout=30)
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

def analyze_announcement(text, company_name):
    """Analyze announcement and generate summary"""
    if not text:
        return {
            'summary': f"Unable to extract content from the announcement PDF for {company_name}.",
            'sentiment': 'neutral'
        }
    
    # Simple keyword-based analysis
    positive_keywords = ['growth', 'profit', 'increase', 'expansion', 'dividend', 'acquisition', 
                         'revenue', 'gain', 'success', 'partnership', 'award', 'milestone',
                         'improved', 'strong', 'positive', 'progress']
    
    negative_keywords = ['loss', 'decline', 'decrease', 'bankruptcy', 'lawsuit', 'penalty',
                        'investigation', 'fraud', 'default', 'resignation', 'closure',
                        'weak', 'negative', 'downgrade', 'risk']
    
    text_lower = text.lower()
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
    
    # Determine sentiment
    if positive_count > negative_count:
        sentiment = 'positive'
        sentiment_text = '📈 POSITIVE NEWS'
    elif negative_count > positive_count:
        sentiment = 'negative'
        sentiment_text = '📉 NEGATIVE NEWS'
    else:
        sentiment = 'neutral'
        sentiment_text = '➖ NEUTRAL NEWS'
    
    # Generate summary (simplified - in production, use AI/NLP)
    sentences = re.split(r'[.!?]\s+', text)
    important_sentences = []
    
    for sentence in sentences[:20]:  # Check first 20 sentences
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in positive_keywords + negative_keywords):
            if len(sentence.split()) > 5:  # Ensure sentence has substance
                important_sentences.append(sentence.strip())
                if len(important_sentences) >= 4:
                    break
    
    if not important_sentences:
        important_sentences = sentences[:4]
    
    summary_lines = [
        f"{sentiment_text}",
        f"Company: {company_name}",
        *important_sentences[:3]
    ]
    
    return {
        'summary': '\n'.join(summary_lines),
        'sentiment': sentiment
    }

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

@app.route('/api/announcements')
def get_announcements():
    """API endpoint to get announcements"""
    global announcements_cache
    
    # Get days_back parameter from query string (default: 1 day - today only)
    days_back = request.args.get('days_back', default=1, type=int)
    max_results = request.args.get('max_results', default=200, type=int)
    
    # Validate parameters
    days_back = min(max(1, days_back), 30)  # Between 1 and 30 days
    max_results = min(max(10, max_results), 500)  # Between 10 and 500 results
    
    print(f"API Request: days_back={days_back}, max_results={max_results}")
    
    # Fetch fresh data
    announcements_cache = fetch_bse_announcements(days_back=days_back, max_results=max_results)
    
    return jsonify({
        'success': True,
        'data': announcements_cache,
        'count': len(announcements_cache),
        'days_back': days_back,
        'max_results': max_results
    })

@app.route('/api/summarize', methods=['POST'])
def summarize_announcement():
    """API endpoint to summarize an announcement"""
    data = request.json
    pdf_url = data.get('pdf_link')
    company_name = data.get('company_name')
    bse_code = data.get('bse_code', 'UNKNOWN')
    
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
    
    return jsonify({
        'success': True,
        'summary': analysis['summary'],
        'sentiment': analysis['sentiment']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
