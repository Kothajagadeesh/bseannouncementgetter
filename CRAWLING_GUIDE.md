# 🕷️ BSE Announcements Crawler - Complete Guide

## Overview

The application now supports **crawling all announcements** from BSE India with flexible date ranges and result limits!

## ✨ New Features

### 1. **Date Range Selection**
Choose how far back to fetch announcements:
- **Today** (last 24 hours)
- **Last 3 Days**
- **Last 7 Days** (default)
- **Last 15 Days**
- **Last 30 Days**

### 2. **Result Limit Control**
Control how many announcements to fetch:
- **50 results** (fast load)
- **100 results** (balanced)
- **200 results** (comprehensive, default)
- **500 results** (maximum, all available)

### 3. **Real-Time Data**
- All data is fetched **live** from BSE India API
- No cached or stale data
- Updated instantly on refresh

## 🎯 How to Use

### Via Web Interface

1. **Open the application** at http://localhost:5000
2. **Select date range** from the "Days" dropdown:
   ```
   [Days: Last 7 Days ▼]
   ```
3. **Select result limit** from the "Limit" dropdown:
   ```
   [Limit: 200 ▼]
   ```
4. **Click "🔄 Refresh Data"** to fetch announcements
5. **Wait** for the data to load (5-10 seconds)
6. **Browse** the complete list with search functionality

### Via API

You can also fetch data programmatically:

```bash
# Get announcements from last 7 days (max 200)
curl "http://localhost:5000/api/announcements?days_back=7&max_results=200"

# Get announcements from last 30 days (max 500)
curl "http://localhost:5000/api/announcements?days_back=30&max_results=500"

# Get today's announcements only (max 100)
curl "http://localhost:5000/api/announcements?days_back=1&max_results=100"
```

### Response Format

```json
{
  "success": true,
  "data": [
    {
      "company_name": "Nestle India Ltd",
      "bse_code": "500790",
      "pdf_link": "https://www.bseindia.com/xml-data/corpfiling/AttachLive/6f345a53-19e1-4c9b-9e5c-0f249ab2027e.pdf",
      "summary": null
    },
    ...
  ],
  "count": 150,
  "days_back": 7,
  "max_results": 200
}
```

## 📊 Data Coverage

### What You Get

- ✅ **Company Name**: Full official name
- ✅ **BSE Code**: 6-digit security code
- ✅ **PDF Link**: Direct link to announcement PDF
- ✅ **Category**: Inferred from announcement type
- ✅ **Timestamp**: When announcement was published

### BSE API Limitations

**Important**: The BSE India API has some inherent limitations:

1. **Per-Request Limit**: 
   - API returns approximately 50 announcements per request
   - Even if you request 30 days, you may only get the latest 50

2. **Date Range Behavior**:
   - The API prioritizes **recent announcements**
   - Older announcements within the date range may not be returned
   - To get historical data, multiple requests would be needed

3. **Workaround**:
   - The app is designed to fetch what's available
   - For comprehensive historical data, consider running periodic fetches
   - Store results in a database for long-term retention

## 🔧 Technical Details

### Backend Implementation

```python
def fetch_bse_live_api(days_back=7, max_results=200):
    """
    Fetches announcements from BSE India API
    
    Args:
        days_back: Number of days to look back (1-30)
        max_results: Maximum results to return (10-500)
    
    Returns:
        List of announcements with company name, BSE code, and PDF link
    """
```

### API Endpoint

```python
@app.route('/api/announcements')
def get_announcements():
    days_back = request.args.get('days_back', default=7, type=int)
    max_results = request.args.get('max_results', default=200, type=int)
    
    # Validate: days_back between 1-30, max_results between 10-500
    # Fetch and return data
```

### Data Flow

```
User Selects Parameters
    ↓
Frontend sends API request
    ↓
Backend validates parameters
    ↓
BSE API called with date range
    ↓
Parse JSON response
    ↓
Extract company names, codes, PDF links
    ↓
Return formatted data
    ↓
Frontend displays in table
```

## 💡 Best Practices

### For Maximum Coverage

1. **Use shorter date ranges** for more complete data:
   - ❌ Don't: 30 days (might miss older announcements)
   - ✅ Do: 7 days (gets recent complete set)

2. **Run periodic fetches** if you need historical data:
   ```python
   # Fetch weekly and store in database
   for week in range(4):
       days_start = week * 7
       days_end = (week + 1) * 7
       announcements = fetch_for_date_range(days_start, days_end)
       store_in_database(announcements)
   ```

3. **Set appropriate limits**:
   - 50-100 for quick browsing
   - 200 for comprehensive view
   - 500 when you need everything available

### For Performance

1. **Cache results** when possible
2. **Use smaller limits** for faster loading
3. **Implement pagination** on frontend for large datasets
4. **Run heavy fetches** during off-peak hours

## 🚀 Example Use Cases

### 1. Daily Monitoring
```javascript
// Fetch today's announcements every hour
setInterval(() => {
    fetch('/api/announcements?days_back=1&max_results=100')
        .then(r => r.json())
        .then(data => processNewAnnouncements(data.data));
}, 3600000); // Every hour
```

### 2. Weekly Report
```python
# Get last week's announcements
announcements = fetch_bse_live_api(days_back=7, max_results=500)

# Group by company
by_company = {}
for ann in announcements:
    company = ann['company_name']
    if company not in by_company:
        by_company[company] = []
    by_company[company].append(ann)

# Generate report
generate_weekly_report(by_company)
```

### 3. Specific Company Tracking
```javascript
// Track specific companies
const watchlist = ['500325', '532540', '500180']; // RIL, TCS, HDFC

async function trackWatchlist() {
    const data = await fetch('/api/announcements?days_back=7&max_results=200');
    const announcements = await data.json();
    
    const relevant = announcements.data.filter(ann => 
        watchlist.includes(ann.bse_code)
    );
    
    console.log(`Found ${relevant.length} announcements for watchlist companies`);
    return relevant;
}
```

## 📝 Summary

✅ **You can now crawl** all available BSE announcements  
✅ **Flexible date ranges** from 1 to 30 days  
✅ **Adjustable limits** from 10 to 500 results  
✅ **Real-time data** fetched live from BSE India  
✅ **Correct PDF links** using ATTACHMENTNAME field  
✅ **Search functionality** to filter results  
✅ **Beautiful UI** with responsive design  

⚠️ **Note**: Due to BSE API limitations, you may get up to 50 announcements per request. For comprehensive historical data, consider multiple requests or database storage.

---

**Ready to crawl! 🕷️ Open http://localhost:5000 and start exploring BSE announcements!**
