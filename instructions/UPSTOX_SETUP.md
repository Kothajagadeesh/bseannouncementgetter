# Upstox API Integration Setup Guide

## 📋 Prerequisites
- Upstox trading account
- Access to Upstox Developer Portal

---

## 🔧 Step-by-Step Setup

### Step 1: Create Upstox App

1. **Visit**: https://upstox.com/developer/apps
2. **Login** with your Upstox credentials
3. Click **"Create App"** or **"Edit Regular App"**

### Step 2: Fill App Details

Based on your screenshot, fill the form as follows:

#### Required Fields:
- **App Name**: `StocksNew` (or any name you prefer)
- **Redirect URL**: `http://localhost:5000/upstox/callback`
  - ⚠️ This MUST match exactly
  - For production, use your domain: `https://yourdomain.com/upstox/callback`

#### Optional Fields (Recommended):
- **Postback URL**: `http://localhost:5000/upstox/postback`
- **Notifier webhook endpoint**: `http://localhost:5000/upstox/notify`
- **Description**: 
  ```
  BSE Announcements Analyzer with live market data integration for F&O trading analysis
  ```

#### Settings:
- **OTP Settings**: ✅ Keep enabled for security

### Step 3: Get API Credentials

After saving your app, you'll receive:

1. **API Key** (Client ID)
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Example: `12345678-1234-1234-1234-123456789012`

2. **API Secret**
   - Keep this secure! Never share publicly
   - Example: `abcdefgh-ijkl-mnop-qrst-uvwxyz123456`

---

## 🔑 Configure Environment Variables

### Option 1: Export in Terminal (Temporary)

```bash
export UPSTOX_API_KEY='your-api-key-here'
export UPSTOX_API_SECRET='your-api-secret-here'
```

### Option 2: Add to ~/.bashrc (Permanent)

```bash
echo "export UPSTOX_API_KEY='your-api-key-here'" >> ~/.bashrc
echo "export UPSTOX_API_SECRET='your-api-secret-here'" >> ~/.bashrc
source ~/.bashrc
```

### Option 3: Create .env file

```bash
# Create .env file in project root
cat > .env << EOF
UPSTOX_API_KEY=your-api-key-here
UPSTOX_API_SECRET=your-api-secret-here
EOF
```

---

## 🚀 Start the Application

Restart your Flask app with all credentials:

```bash
OPENAI_API_KEY='your-openai-key' \
SLACK_BOT_TOKEN='your-slack-token' \
SLACK_CHANNEL='#trade-opportunity' \
UPSTOX_API_KEY='your-upstox-api-key' \
UPSTOX_API_SECRET='your-upstox-api-secret' \
python3 app.py
```

---

## 🔐 Authenticate with Upstox

### First-Time Authentication:

1. **Start the app** (as shown above)

2. **Visit**: http://localhost:5000/upstox/login

3. **Login** with your Upstox credentials

4. **Grant permissions** to your app

5. You'll be **redirected back** to your app

6. **Access Token** will be automatically saved

### What Happens:
- OAuth 2.0 flow authenticates your app
- Access token is stored in session and environment
- Token is valid for 24 hours
- Automatically used for all API requests

---

## 📊 Access Live Market Data

### View Dashboard:
```
http://localhost:5000/upstox/live-data
```

### Features Available:
- ✅ Real-time stock quotes
- ✅ Multi-symbol tracking
- ✅ Auto-refresh every 30 seconds
- ✅ OHLC data (Open, High, Low, Close)
- ✅ Volume information
- ✅ Percentage change with colors

### Sample Symbols:
```
RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, BHARTIARTL, SBIN, ITC, LT
```

---

## 🔄 API Endpoints Available

### Authentication:
- `GET /upstox/login` - Start OAuth flow
- `GET /upstox/callback` - OAuth callback (automatic)

### Data Fetching:
- `GET /api/upstox/status` - Check auth status
- `GET /api/upstox/quote/<symbol>` - Single quote
- `GET /api/upstox/quotes?symbols=RELIANCE,TCS` - Multiple quotes

### Example API Call:
```bash
curl http://localhost:5000/api/upstox/quotes?symbols=RELIANCE,TCS,INFY
```

---

## 🛠️ Troubleshooting

### Issue: "API Key not configured"
**Solution**: Set `UPSTOX_API_KEY` and `UPSTOX_API_SECRET` environment variables

### Issue: "Not authenticated"
**Solution**: Visit `/upstox/login` to authenticate

### Issue: "Invalid redirect_uri"
**Solution**: Ensure redirect URI in Upstox app matches exactly:
- Dev: `http://localhost:5000/upstox/callback`
- Prod: `https://yourdomain.com/upstox/callback`

### Issue: "Access token expired"
**Solution**: 
- Access tokens expire after 24 hours
- Re-authenticate via `/upstox/login`
- Future: Implement refresh token flow

### Issue: Symbol not found
**Solution**: 
- Use NSE symbols (e.g., `RELIANCE` not `RELIANCE.NS`)
- Ensure symbol is traded on NSE
- Check for correct spelling

---

## 📖 API Documentation

Full Upstox API documentation:
- **Docs**: https://upstox.com/developer/api-documentation
- **Interactive API**: https://upstox.com/developer/api-documentation/open-api

---

## 💡 Tips

### Best Practices:
1. **Never commit** API keys or secrets to git
2. **Use environment variables** for all credentials
3. **Re-authenticate daily** (tokens expire in 24h)
4. **Rate Limits**: Upstox has API rate limits - avoid excessive calls
5. **Market Hours**: Data is most accurate during market hours (9:15 AM - 3:30 PM IST)

### For Production:
1. Use HTTPS for callback URLs
2. Implement refresh token flow
3. Add error handling for network issues
4. Cache frequently accessed data
5. Set up monitoring for API failures

---

## 🔗 Quick Links

- **Upstox Developer Portal**: https://upstox.com/developer/apps
- **API Documentation**: https://upstox.com/developer/api-documentation
- **Support**: https://upstox.com/support

---

## 📝 Notes

- **API Calls**: Limited per day (check your plan)
- **Data Delay**: Real-time for most users, may have slight delays
- **Instruments**: Supports Equity, Futures, Options, Currency, Commodity
- **Exchanges**: NSE, BSE, MCX, CDS

---

**Last Updated**: 2025-12-11
**Status**: Production Ready ✅
