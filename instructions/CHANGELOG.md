# BSE Announcements Analyzer - Changelog

## Project Overview
Real-time BSE (Bombay Stock Exchange) announcement monitoring and analysis system with AI-powered sentiment analysis, automatic Slack notifications, and NSE index filtering.

---

## [2025-12-11] - Latest Version

### 📈 Added - Options Chain Viewer with Live Data
- **New Feature**: Interactive options chain viewer for all F&O stocks with real-time market data
- **Smart Filtering**: Automatically filters out expired options (shows only active)
- **Live Market Data**: 
  - Underlying stock: LTP, Today's Range (High-Low), color-coded price movement
  - Options: LTP, Volume, Open Interest from Upstox API
- **Features**:
  - Autocomplete search for 208 F&O stock symbols
  - Fetches live options data from Upstox API
  - Tabs for viewing: All Options, Call Options (CE), Put Options (PE)
  - Displays: Strike Price, Expiry Date, LTP, Volume, Open Interest, Trading Symbol
  - Real-time stats: Total Options, Call Count, Put Count
  - Filters expired options based on current date
  - **Column-level filters**: Filter by Type, Strike Price, Expiry, LTP, Volume, OI, Symbol
- **User-Friendly UI**:
  - Search with autocomplete suggestions
  - Beautiful table layout with color-coded badges
  - Responsive design
  - Loading states and error handling
- **Routes**:
  - `GET /options-chain` - Viewer page
  - `GET /api/options-chain/<symbol>` - Fetch options API
  - `GET /api/fo-symbols` - Get F&O symbols list
- **Files Created**:
  - `templates/options-chain.html` - Options viewer interface
- **Files Modified**:
  - `app.py`: Added routes for options chain
  - `templates/index.html`: Added navigation button

### 🔄 Updated - F&O Stocks List from NSE Official API
- **Major Update**: Replaced F&O stocks list with official NSE India data
- **Previous**: 83 stocks (manually curated)
- **Current**: **208 stocks** (+125 new stocks!)
- **Source**: NSE India Official API - `equity-stockIndices?index=SECURITIES%20IN%20F%26O`
- **New Additions Include**:
  - 360ONE, ABB, ADANIGREEN, ANGELONE, DIXON, KAYNES, and 119 more
  - Includes newly added F&O stocks that were missing
- **Data Structure**:
  - NSE Symbol (primary)
  - Company Name
  - ISIN Code
  - Sector
  - BSE Code (when available)
- **Files**:
  - Created: `resources/update_fo_stocks_from_nse.py` - Auto-updater script
  - Updated: `resources/fo_stocks.json` - Now with 208 stocks
  - Backup: `resources/fo_stocks_old_backup.json` - Old 83 stocks list
  - Created: `resources/fo_stocks_nse.json` - Raw NSE data
- **Code Updates**:
  - `app.py`: Updated `load_fo_stocks()` to handle NSE-based structure
  - `templates/index.html`: Updated count to 208 stocks

### 📊 Added - BSE Instruments Browser
- **New Feature**: Interactive browser for all 27,000+ BSE instruments from Upstox
- **Data Source**: Fetches live data from Upstox's complete instruments list
- **Features**:
  - Displays all BSE instruments in a searchable, filterable table
  - Column-level filters for precise searching
  - DataTables integration with pagination and sorting
  - Shows: Trading Symbol, Name, Segment, ISIN, Type, Instrument Key, Lot Size, Tick Size
  - Color-coded badges for different instrument types
  - Real-time stats display
- **Purpose**: Debug and find correct instrument keys for Upstox API calls
- **Routes**:
  - `GET /bse-instruments` - Browser page
  - `GET /api/bse-instruments` - API endpoint
- **Files Created**:
  - `templates/bse-instruments.html` - Interactive table with filters
- **Files Modified**:
  - `app.py`: Added routes for BSE instruments
  - `templates/index.html`: Added navigation button

### 📚 Refactored - Project Structure Reorganization
- **Major Refactoring**: Reorganized project structure for better maintainability
- **New Directory Structure**:
  ```
  bseannouncementgetter/
  ├── integrations/             # All third-party API integrations
  │   ├── __init__.py
  │   ├── slack_integration.py
  │   ├── telegram_integration.py
  │   └── upstox_integration.py
  ├── resources/                # Data files and JSON resources
  │   ├── fo_stocks.json
  │   ├── fo_instrument_keys.json
  │   ├── fetch_fo_instrument_keys.py
  │   └── BSE.json
  ├── instructions/             # Documentation and setup guides
  │   ├── CHANGELOG.md
  │   ├── UPSTOX_SETUP.md
  │   └── SLACK_TELEGRAM_SETUP.md
  ├── templates/                # HTML templates
  ├── app.py                    # Main Flask application
  ├── nse_indices.py
  └── market_cap_data.py
  ```
- **Benefits**:
  - Better code organization and separation of concerns
  - Easier to maintain and extend integrations
  - Clearer project structure for new developers
  - Centralized resource management
- **Files Modified**:
  - `app.py`: Updated imports to use new module structure
  - Moved: `upstox_integration.py` → `integrations/`
  - Created: `integrations/slack_integration.py` (extracted from app.py)
  - Created: `integrations/telegram_integration.py` (extracted from app.py)
  - Created: `integrations/__init__.py`
  - Moved: `*.json` files → `resources/`
  - Moved: `*.md` files → `instructions/`

### 🔄 Updated - Expected Return Input to Dropdown
- **Improved UX**: Changed Expected Monthly Return from number input to dropdown
- **Options**: 1%, 2%, 5%, 10% with risk level descriptions
- **Default**: 2% (Moderate)
- **Benefit**: Simplified user experience with predefined, realistic return targets
- **Files Modified**:
  - `templates/fando-club.html`: Replaced input field with select dropdown

### 🗑️ Removed - Position Size Calculator
- **Removed Feature**: Simple position size calculator from F&O Club page
- **Reason**: Streamlined interface to focus on AI Options Trading Advisor
- **Replaced By**: AI-powered recommendations provide more comprehensive trading strategies
- **Files Modified**:
  - `templates/fando-club.html`: Removed calculator form, JavaScript handlers, and result display

### 🤖 Added - AI Options Trading Advisor
- **Major Feature**: AI-powered options trading recommendations using GPT-4
- **Purpose**: Help users achieve target returns with optimal options strategies
- **User Inputs**:
  - Investment Capital (₹10,000+)
  - Expected Monthly Return (%)
  - Risk Tolerance (Conservative/Moderate/Aggressive)
- **AI Analysis**:
  - Fetches real-time options data from Upstox for top F&O stocks
  - Sends data to GPT-4o-mini with trading context
  - Generates actionable buy/sell recommendations
  - Specifies: Symbol, Option Type (CE/PE), Strike Price, Expiry, Expected Profit
- **Features**:
  - Real-time market data integration
  - Risk-adjusted strategies
  - Detailed reasoning for each recommendation
  - User-friendly interface in F&O Club page
- **API Endpoint**: `POST /api/options-advisor`
- **Files Modified**:
  - `upstox_integration.py`: Added `get_options_chain()` and `get_all_fo_options_summary()` methods
  - `app.py`: Added `/api/options-advisor` endpoint with OpenAI integration
  - `templates/fando-club.html`: Added AI Advisor form and results display
- **Requirements**:
  - Upstox authentication (OAuth)
  - OpenAI API key configured
  - Active market data access

### 🔄 Updated - Expanded F&O Stock Instrument Keys
- **Expanded Coverage**: Increased from 20 to **77 F&O eligible stocks**
- **Coverage**: 93% of all F&O eligible stocks (77 out of 83)
- **Stocks Added**: ACC, ADANIPORTS, APOLLOHOSP, ASIANPAINT, BAJFINANCE, BAJAJFINSV, and 50+ more
- **Automated Generation**: Created `fetch_fo_instrument_keys.py` script to generate mappings
- **Data File**: Saved to `fo_instrument_keys.json` for reference
- **Missing Stocks**: 6 stocks pending ISIN codes (ABB, BANKBARODA, UNIONBANK, ADANIGREEN, MRF, PVRINOX)
- **Files Modified**:
  - `upstox_integration.py`: Updated STOCK_INSTRUMENT_KEYS dictionary
  - Created: `fetch_fo_instrument_keys.py` (generator script)
  - Created: `fo_instrument_keys.json` (mapping data)

### 📊 Added - Upstox Live Market Data Integration
- **New Feature**: Real-time market data from Upstox API
- **New Module**: `upstox_integration.py` - Handles Upstox API authentication and data fetching
- **New Page**: `/upstox/live-data` - Live market quotes dashboard
- **Features**:
  - OAuth 2.0 authentication flow with Upstox
  - Real-time stock quotes (LTP, change, volume, OHLC)
  - Multi-symbol quote fetching
  - Auto-refresh every 30 seconds
  - Beautiful card-based UI with live price updates
  - Color-coded positive/negative changes
  - User profile integration
  - Instrument search functionality
- **API Routes Added**:
  - `GET /upstox/login` - Initiate OAuth flow
  - `GET /upstox/callback` - Handle OAuth callback
  - `GET /upstox/live-data` - Live data dashboard page
  - `GET /api/upstox/status` - Check authentication status
  - `GET /api/upstox/quote/<symbol>` - Get single quote
  - `GET /api/upstox/quotes` - Get multiple quotes
- **Configuration**:
  - `UPSTOX_API_KEY`: API key from Upstox developer portal
  - `UPSTOX_API_SECRET`: API secret
  - `UPSTOX_ACCESS_TOKEN`: Access token (obtained via OAuth)
- **Setup Guide**:
  1. Create app at https://upstox.com/developer/apps
  2. Set redirect URI to `http://localhost:5000/upstox/callback`
  3. Set environment variables for API key and secret
  4. Visit `/upstox/login` to authenticate
- **Files**:
  - Created: `upstox_integration.py` (API integration module)
  - Created: `templates/upstox-live.html` (live data dashboard)
  - Modified: `app.py` (added Upstox routes and imports)
  - Modified: `templates/index.html` (added Live Data navigation button)
  - Modified: `.env.example` (added Upstox configuration)

### 🆕 Added - F&O Club Calculator Page
- **New Page**: `/fando-club` - Position size calculator
- **Features**:
  - Input field for investment amount
  - Dropdown for risk percentage (1%, 2%, 5%, 10%)
  - Real-time calculation of maximum risk amount
  - Beautiful UI matching the main dashboard theme
  - Navigation button in main dashboard banner
  - Risk management tips and recommendations
- **Files**:
  - Created: `templates/fando-club.html`
  - Modified: `app.py` (added route for F&O Club)
  - Modified: `templates/index.html` (added navigation button)

---

## [2025-12-10] - Major Feature Additions

### 🤖 OpenAI Integration
- **GPT-4o-mini Integration**: Added AI-powered analysis using OpenAI's GPT-4o-mini model
- **Features**:
  - Intelligent sentiment analysis (Positive/Negative/Neutral)
  - Context-aware summaries of announcements
  - Financial terminology understanding
  - Fallback to Python-based analysis if API key not set
- **Configuration**: Set via `OPENAI_API_KEY` environment variable

### 📅 BSE Published Time in Slack
- **Added**: BSE announcement published timestamp to Slack notifications
- **Format**: Shows exact date and time when BSE published the announcement
- **Display**: `📅 Published: Dec 10, 2025 09:58 PM`
- **Files Modified**:
  - `app.py`: Updated `send_to_slack()` function
  - `templates/index.html`: Updated JavaScript to pass date_time

### 🕐 Last Refresh Timestamp
- **Added**: Real-time "Last Refreshed" indicator in browser UI
- **Location**: Controls section, next to refresh button
- **Format**: `YYYY-MM-DD HH:MM:SS` (includes seconds)
- **Updates**: Automatically on refresh and background checks
- **Files Modified**:
  - `app.py`: Added `last_refresh_time` tracking
  - `templates/index.html`: Added display element and JavaScript update

### 💬 Simplified Slack Notifications
- **Improved**: Streamlined Slack message format for quick decision-making
- **New Format**:
  ```
  🏛️ Company Name
  BSE: 500325 | Sentiment: 📈 POSITIVE
  📅 Published: Dec 10, 2025 09:58 PM
  📄 View PDF
  ```
- **Benefits**: Faster scanning, less clutter, mobile-friendly

### 🔔 Automatic Notification System
- **Major Feature**: Auto-notification system for Nifty index stocks
- **Intelligent Scheduling**:
  - Market hours (9:00 AM - 3:30 PM IST): Check every **1 minute**
  - Off-hours (3:31 PM - 8:59 AM IST): Check every **10 minutes**
- **Smart Filtering**:
  - Auto-send to Slack: Nifty 50, Nifty Next 50, Nifty 500 stocks
  - Manual summarize: Other stocks (click button in UI)
- **Duplicate Prevention**: Tracks sent announcements to avoid spam
- **Implementation**:
  - Added: APScheduler library
  - Added: Background job scheduler with cron triggers
  - Added: `auto_check_and_notify()` function
  - Modified: `send_to_slack()` to support auto-notifications

### 📊 NSE Indices Integration
- **New Module**: `nse_indices.py` - Fetches and caches NSE index data
- **Indices Loaded**:
  - Nifty 50 (51 stocks)
  - Nifty Next 50 (50 stocks)
  - Nifty 500 (502 stocks)
- **Features**:
  - Smart caching (24-hour validity)
  - Symbol lookup functionality
  - BSE to NSE code mapping
- **UI Updates**:
  - Index badges on announcements (N50, Next50, N500)
  - NSE symbol display below company name
  - Color-coded badges (Green, Orange, Blue)

### 🏷️ Index Filter Pills
- **New Feature**: Interactive filter buttons at top of dashboard
- **Filter Options**:
  - 🎯 All Stocks
  - 🟢 Nifty 50
  - 🟠 Nifty Next 50
  - 🔵 Nifty 500
- **Dynamic Counters**: Shows real-time count of announcements per index
- **Combined Filtering**: Works together with search functionality
- **Files Modified**:
  - `templates/index.html`: Added filter pills UI and JavaScript

### 🔍 Enhanced Search
- **Improved**: Search now works in conjunction with index filters
- **Logic**: First applies index filter, then search term
- **User Experience**: Seamless filtering experience

---

## Core Features (Initial Implementation)

### 📰 Live BSE Data Fetching
- **Source**: BSE India Official API
- **Refresh**: Configurable (default: today's announcements)
- **Data Points**: Company name, BSE code, PDF link, date/time, market cap

### 💬 Slack Integration
- **Configuration**: 
  - `SLACK_BOT_TOKEN`: Bot authentication token
  - `SLACK_CHANNEL`: Target channel (default: #trade-opportunity)
- **Required Scopes**: `chat:write`, `chat:write.public`
- **Format**: Concise message blocks with company info and sentiment

### 📱 Telegram Integration (Optional)
- **Configuration**:
  - `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
  - `TELEGRAM_CHAT_ID`: Target chat/group ID
- **Status**: Configured but currently using Slack as primary

### 🎯 F&O Stock Filtering
- **Data Source**: `fo_stocks.json` (183 F&O eligible stocks)
- **Features**: Badges, market cap categorization, fast lookup

### 📄 PDF Management
- **Download**: Automatic PDF download from BSE
- **Storage**: Local caching in `announcements_pdfs/YYYYMMDD/`
- **Serving**: Flask route to serve cached PDFs
- **Analysis**: Text extraction for AI analysis

### 🎨 Modern UI
- **Design**: Purple gradient theme, responsive layout
- **Components**: 
  - Search box with live filtering
  - Days/limit selectors
  - Announcement table with badges
  - Modal for summaries
- **Framework**: Vanilla JavaScript, no dependencies

### 🔐 Environment Configuration
- **Required**:
  - `OPENAI_API_KEY`: For GPT analysis
  - `SLACK_BOT_TOKEN`: For Slack notifications
  - `SLACK_CHANNEL`: Target Slack channel
- **Optional**:
  - `TELEGRAM_BOT_TOKEN`: For Telegram notifications
  - `TELEGRAM_CHAT_ID`: Target Telegram chat

---

## File Structure

```
bseannouncementgetter/
├── app.py                      # Main Flask application
├── nse_indices.py              # NSE indices data fetcher
├── market_cap_data.py          # Market cap information
├── requirements.txt            # Python dependencies
├── fo_stocks.json              # F&O eligible stocks data
├── CHANGELOG.md                # This file
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variable template
├── SLACK_TELEGRAM_SETUP.md     # Integration setup guide
├── templates/
│   ├── index.html              # Main dashboard
│   └── fando-club.html         # F&O Club calculator
├── nse_cache/                  # NSE indices cache (gitignored)
│   ├── nifty50.json
│   ├── niftynext50.json
│   └── nifty500.json
└── announcements_pdfs/         # Cached PDFs (gitignored)
    └── YYYYMMDD/
```

---

## API Endpoints

### Public Routes
- `GET /` - Main dashboard
- `GET /fando-club` - F&O Club calculator page
- `GET /pdf/<path:filepath>` - Serve cached PDFs

### API Routes
- `GET /api/announcements` - Get BSE announcements
  - Query params: `days_back`, `max_results`
  - Returns: Announcements with NSE indices, last_refresh time
- `POST /api/summarize` - Analyze announcement
  - Body: `pdf_link`, `company_name`, `bse_code`, `date_time`
  - Returns: Sentiment, summary, delivery status
- `GET /api/nse-indices` - Get all NSE indices data
- `GET /api/nse-indices/<index_name>` - Get specific index
- `GET /api/check-symbol/<symbol>` - Check which indices a symbol belongs to

---

## Dependencies

```
Flask==3.0.0
requests==2.31.0
beautifulsoup4==4.12.2
PyPDF2==3.0.1
lxml==4.9.3
selenium==4.15.2
webdriver-manager==4.0.1
openai==2.9.0
slack-sdk==3.27.1
python-telegram-bot==20.8
APScheduler==3.10.4
```

---

## Configuration Notes

### Auto-Notification Schedule
- **Market Hours**: 9:00 AM - 3:30 PM IST (every 1 minute)
- **Off-Hours**: 3:31 PM - 8:59 AM IST (every 10 minutes)
- **Timezone**: Asia/Kolkata (IST)

### OpenAI Usage
- **Model**: gpt-4o-mini
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Estimated Daily Cost**: $0.01 - $0.05 (for 10-20 announcements/day)

### Cache Management
- **NSE Indices**: 24-hour cache validity
- **PDFs**: Permanent local storage by date
- **Announcements**: In-memory cache, refreshed on API calls

---

## Future Enhancement Ideas

- [ ] Email notifications support
- [ ] WhatsApp integration
- [ ] Advanced filtering by market cap/sector
- [ ] Historical data analysis
- [ ] Custom alert rules
- [ ] Portfolio tracking
- [ ] Performance metrics dashboard
- [ ] Export to CSV/Excel
- [ ] Mobile app (React Native/Flutter)
- [ ] Multi-user support with authentication

---

## Notes

- All timestamps are in IST (Indian Standard Time)
- The app runs 24/7 with background scheduler
- Duplicate announcements are automatically filtered
- Only Nifty index stocks trigger auto-notifications
- Manual summarize available for all stocks via UI

---

**Last Updated**: 2025-12-11 10:05:00 IST
**Maintainer**: Jagadeesh
**Status**: Production Ready ✅
