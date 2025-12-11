# OpenAI Integration Setup

## Overview
The app now uses **OpenAI GPT-3.5-turbo** to analyze BSE announcement PDFs and provide sentiment analysis.

## Setup Instructions

### 1. Get Your OpenAI API Key
- Go to: https://platform.openai.com/api-keys
- Sign in or create an account
- Click "Create new secret key"
- Copy your API key (it starts with `sk-...`)

### 2. Set the API Key

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY='your-api-key-here'
python3 app.py
```

**Option B: Permanent Setup (Linux)**
Add to your `~/.bashrc` or `~/.profile`:
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Option C: Using .env file**
```bash
# Create .env file
echo 'OPENAI_API_KEY=your-api-key-here' > .env

# Then load it before running
export $(cat .env | xargs)
python3 app.py
```

## How It Works

When you click "Summarize" on any announcement:
1. 📥 **PDF is downloaded** locally to `announcements_pdfs/YYYYMMDD/`
2. 📄 **Text is extracted** from the PDF (first 5 pages)
3. 🤖 **Sent to OpenAI** with this prompt:
   ```
   "You are an expert stock market analyst. Read the PDF content 
   and suggest Positive, Negative or Neutral. Don't provide any explanation."
   ```
4. ✅ **Returns**: Simply **Positive**, **Negative**, or **Neutral**

## Cost Estimate
- GPT-3.5-turbo: ~$0.0005-0.002 per request
- Very affordable for analyzing announcements!

## Testing
To test if it's working:
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Should show your key (not empty)
```

## Fallback Behavior
If the OpenAI API key is not set, the app will show:
```
"OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
```

## Security Notes
- ⚠️ Never commit your API key to Git
- ⚠️ Keep your API key private
- ✅ Use environment variables (not hardcoded)
