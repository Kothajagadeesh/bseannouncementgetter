# 📊 BSE Announcements Analyzer

A beautiful web application that fetches real-time announcements from BSE India, extracts company information, and provides AI-powered sentiment analysis of announcement PDFs.

## ✨ Features

- **🤖 Advanced Web Scraping**: Uses Selenium for dynamic JavaScript content from BSE India
- **📊 Dual Data Sources**: Fetches from both BSE India AND NSE India with automatic fallback
- **🔄 Smart Fallback System**: BSE → NSE → Sample data (always reliable)
- **🔍 Search Functionality**: Quick search by company name or BSE code
- **🎨 Beautiful UI**: Modern, responsive design with gradient themes
- **📄 PDF Analysis**: Automatically extracts and analyzes PDF content
- **📈 Sentiment Analysis**: Determines if news is positive, negative, or neutral
- **✨ Animated Loading**: Beautiful sparkles and spinner animations during analysis
- **📝 5-Line Summaries**: Concise summaries of announcement content
- **⚡ Headless Browser**: Chrome runs in background for efficient scraping

## 🚀 Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

1. **Start the Flask server**:
```bash
python app.py
```

2. **Open your browser** and navigate to:
```
http://localhost:5000
```

3. **Use the application**:
   - Click "🔄 Refresh Data" to fetch latest announcements
   - Use the search box to filter by company name or BSE code
   - Click "✨ Summarize" on any announcement to analyze it
   - Enjoy the beautiful animations while AI analyzes the content!

## 📋 Technical Details

### Backend (Flask)
- **Web Scraping**: 
  - 🤖 Selenium WebDriver for dynamic BSE India content
  - 📊 NSE India API for alternative data source
  - 🌐 BeautifulSoup4 for HTML parsing
  - 🔄 Smart fallback mechanism (BSE → NSE → Sample)
- **PDF Processing**: PyPDF2 for text extraction from announcements
- **Sentiment Analysis**: Keyword-based analysis (upgradeable to AI/ML models)
- **RESTful API**: Clean API endpoints for frontend communication
- **Browser Automation**: Headless Chrome with automatic ChromeDriver management

### Frontend
- **Pure JavaScript**: No framework dependencies
- **Responsive Design**: Works on desktop and mobile
- **Real-time Search**: Instant filtering of announcements
- **Modal Animations**: Smooth transitions and sparkle effects

## 🔧 Configuration

The application uses the following default settings:
- **Host**: 0.0.0.0 (accessible from network)
- **Port**: 5000
- **Debug Mode**: Enabled (disable in production)

## 📦 Project Structure

```
Shares_chat_bot/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Frontend HTML/CSS/JS
```

## 🎨 Features Breakdown

### 1. Web Scraping
- Mimics real browser behavior with appropriate headers
- Handles dynamic content from BSE India website
- Extracts company name, BSE code, and PDF links

### 2. PDF Analysis
- Downloads and parses PDF announcements
- Extracts text from first 5 pages
- Performs keyword-based sentiment analysis

### 3. User Interface
- **Search Bar**: Real-time filtering
- **Data Table**: Clean, sortable display
- **Analysis Modal**: Beautiful popup with animations
- **Loading States**: Spinner and sparkle animations

### 4. Sentiment Analysis
- Positive indicators: growth, profit, revenue, etc.
- Negative indicators: loss, decline, lawsuit, etc.
- Visual feedback with color-coded results

## 🔐 Security Notes

- Uses browser-like headers for ethical web scraping
- Respects robots.txt and rate limiting
- No sensitive data is stored permanently

## 🚧 Future Enhancements

- Integration with advanced NLP models (GPT, BERT)
- Historical data tracking and trends
- Email alerts for specific companies
- Export functionality (CSV, Excel)
- Real-time WebSocket updates
- Multi-language support

## 📝 License

This project is for educational purposes. Please respect BSE India's terms of service when scraping their website.

## 👨‍💻 Developer Notes

To enhance the sentiment analysis, consider integrating:
- OpenAI GPT API for better summaries
- FinBERT for financial sentiment analysis
- Custom ML models trained on financial data

---

**Made with ❤️ by an AI-powered website builder and stock market analyst**
