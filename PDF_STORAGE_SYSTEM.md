# 📁 Local PDF Storage System

## Overview

Implemented automatic PDF download and local storage system for BSE announcements. PDFs are now downloaded from BSE servers and stored locally for faster access and offline availability.

---

## 🎯 Features

### **1. Automatic PDF Download**
- When a new F&O announcement is fetched, the PDF is automatically downloaded
- Stored in organized folder structure by date
- Unique filename prevents duplicates

### **2. Local File Serving**
- PDFs are served from local storage (much faster than BSE servers)
- No dependency on BSE server availability
- Offline access to downloaded announcements

### **3. Fallback System**
- If local PDF is available → Use local file
- If local download failed → Fall back to BSE link
- Never breaks user experience

---

## 📂 Folder Structure

```
Shares_chat_bot/
├── announcements_pdfs/
│   ├── 20251203/
│   │   ├── 500325_Reliance_Industries_Ltd_20251203_093045_a1b2c3d4.pdf
│   │   ├── 500180_HDFC_Bank_Ltd_20251203_093046_e5f6g7h8.pdf
│   │   └── 532540_Tata_Consultancy_Services_20251203_093047_i9j0k1l2.pdf
│   ├── 20251204/
│   │   └── ...
│   └── 20251205/
│       └── ...
```

### **Filename Format:**
```
{BSE_CODE}_{COMPANY_NAME}_{TIMESTAMP}_{URL_HASH}.pdf

Example:
500325_Reliance_Industries_Ltd_20251203_093045_a1b2c3d4.pdf
```

**Components:**
- `500325` - BSE code
- `Reliance_Industries_Ltd` - Sanitized company name (max 50 chars)
- `20251203_093045` - Download timestamp (YYYYMMDD_HHMMSS)
- `a1b2c3d4` - 8-char hash of original URL (ensures uniqueness)

---

## 🔧 Implementation Details

### **1. PDF Download Function** (`app.py`)

```python
def download_pdf_locally(pdf_url, company_name, bse_code):
    """
    Downloads PDF from BSE and saves locally
    
    Process:
    1. Create safe filename from company name + BSE code
    2. Create date-based folder structure
    3. Check if file already exists (skip if yes)
    4. Download PDF from BSE
    5. Save to local folder
    6. Return local file path
    """
```

**Features:**
- ✅ Automatic folder creation
- ✅ Duplicate detection (won't re-download)
- ✅ Error handling (returns None if fails)
- ✅ File size logging
- ✅ Progress reporting

### **2. Flask PDF Serving Route**

```python
@app.route('/pdf/<path:filepath>')
def serve_pdf(filepath):
    """
    Serves PDFs from local storage
    
    Security:
    - Path restricted to announcements_pdfs folder only
    - Returns 404 if file not found
    - Proper MIME type (application/pdf)
    """
```

### **3. Frontend PDF Link Logic**

```javascript
// Priority order:
1. If local_pdf_path exists → Use local file ✅
2. Else if pdf_link exists → Use BSE link ⚠️
3. Else → Show "N/A" ❌
```

---

## 📊 Data Flow

```
New Announcement Detected
    ↓
Extract PDF URL from BSE API
    ↓
Check if F&O eligible
    ↓ (Yes)
Download PDF from BSE
    ↓
Save to: announcements_pdfs/YYYYMMDD/filename.pdf
    ↓
Store local_pdf_path in announcement data
    ↓
Frontend displays: "📄 View PDF (Local)"
    ↓
User clicks → Opens from local storage
```

---

## 🎨 UI Changes

### **PDF Link Display:**

**With Local PDF:**
```
📄 View PDF (Local)
```
- Green "(Local)" indicator
- Links to `/pdf/20251203/filename.pdf`
- Opens from local Flask server

**Without Local PDF (Fallback):**
```
📄 View PDF
```
- Standard link
- Links to BSE server directly

---

## 💾 Storage Management

### **Disk Space Usage:**

**Average PDF Size:** 150-300 KB per announcement

**Daily Estimates:**
- 10 F&O announcements/day = ~2-3 MB/day
- 30 days = ~60-90 MB/month
- 365 days = ~700 MB - 1 GB/year

### **Cleanup Strategy (Optional):**

You can add automatic cleanup for old PDFs:

```python
# Delete PDFs older than 30 days
def cleanup_old_pdfs(days=30):
    cutoff_date = datetime.now() - timedelta(days=days)
    # Remove folders older than cutoff_date
```

---

## 🚀 Benefits

### **1. Speed**
- **Local access**: Instant loading
- **No BSE dependency**: No waiting for external server
- **Cached**: No repeated downloads

### **2. Reliability**
- **Always available**: Even if BSE server is down
- **Offline access**: PDFs available without internet
- **Backup**: Automatic archive of all announcements

### **3. User Experience**
- **Faster PDF loading**: Local files load instantly
- **Better reliability**: No broken BSE links
- **Clear indication**: "(Local)" badge shows it's from cache

---

## 🔍 Console Output Example

```
================================================================================
FETCHING LIVE BSE ANNOUNCEMENTS...
================================================================================

✅ BSE API SUCCESS! Found 50 announcements
Filtering for F&O eligible stocks only...

🔽 Downloading PDF for Reliance Industries (500325)...
   ✅ Downloaded: 500325_Reliance_Industries_Ltd_20251203_093045_a1b2c3d4.pdf (245.3 KB)

🔽 Downloading PDF for HDFC Bank (500180)...
   📄 PDF already exists: 500180_HDFC_Bank_Ltd_20251203_093046_e5f6g7h8.pdf

🔽 Downloading PDF for TCS (532540)...
   ✅ Downloaded: 532540_Tata_Consultancy_Services_20251203_093047_i9j0k1l2.pdf (189.7 KB)

✅ F&O Filter Results:
   - F&O Eligible: 12 announcements
   - Non-F&O Skipped: 38 announcements
   - Total Returned: 12 F&O stocks only
```

---

## 📝 File Locations

### **Downloaded PDFs:**
```
/Users/jagadeesh.kotha/Shares_chat_bot/announcements_pdfs/
```

### **Backend Code:**
- PDF download function: `app.py` (lines ~55-95)
- PDF serving route: `app.py` (lines ~528-545)
- Download integration: `app.py` (lines ~235-240)

### **Frontend Code:**
- PDF link logic: `templates/index.html` (lines ~585-591)

---

## 🛠️ Testing

### **1. Check Downloaded PDFs:**
```bash
ls -lh announcements_pdfs/20251203/
```

### **2. Test Local PDF Access:**
```
http://localhost:5000/pdf/20251203/500325_Reliance_Industries_Ltd_20251203_093045_a1b2c3d4.pdf
```

### **3. View Download Logs:**
Check Flask console for:
- "✅ Downloaded:" messages
- "📄 PDF already exists:" messages
- "❌ Error downloading:" messages

---

## 🎯 Next Steps (Optional Enhancements)

1. **PDF Compression**: Compress PDFs to save space
2. **Database Index**: Track all downloaded PDFs in SQLite
3. **Search in PDFs**: Full-text search across all PDFs
4. **Thumbnail Generation**: Show PDF preview thumbnails
5. **Bulk Download**: Download all day's PDFs at once
6. **Export Feature**: Export all PDFs as ZIP
7. **Storage Stats**: Dashboard showing storage usage
8. **Auto-cleanup**: Delete PDFs older than X days

---

## ✅ Success Metrics

- ✅ PDFs downloaded automatically for all F&O announcements
- ✅ Organized by date in folders
- ✅ Unique filenames prevent conflicts
- ✅ Local serving working (faster access)
- ✅ Fallback to BSE link if download fails
- ✅ Clear UI indication of local vs remote PDFs
- ✅ No breaking changes to existing functionality

---

## 🎉 Result

**Users now get:**
- **Instant PDF access** from local storage
- **Offline availability** of announcements
- **Automatic backup** of all F&O announcement PDFs
- **Better reliability** - no dependency on BSE servers
- **Clear indication** when using cached vs live PDFs

**Perfect for traders who need fast, reliable access to announcement documents!** 📁⚡
