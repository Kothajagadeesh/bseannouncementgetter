# Slack & Telegram Integration Setup

## Overview
When you click **"Summarize"** on any announcement, the app will:
1. Download and analyze the PDF using OpenAI
2. **Automatically send the summary to Slack** (if configured)
3. **Automatically send the summary to Telegram** (if configured)

---

## 🔵 Slack Setup

### Step 1: Create a Slack App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: `BSE Announcements Bot`
4. Choose your workspace
5. Click **"Create App"**

### Step 2: Add Bot Token Scopes
1. Go to **"OAuth & Permissions"** (left sidebar)
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `chat:write` (Send messages)
   - `chat:write.public` (Send to public channels without joining)

### Step 3: Install App to Workspace
1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

### Step 4: Get Channel Name
1. Open Slack
2. Go to the channel where you want announcements (e.g., `#bse-announcements`)
3. Note the channel name with `#` (e.g., `#bse-announcements`)

### Step 5: Set Environment Variables
```bash
export SLACK_BOT_TOKEN='xoxb-your-token-here'
export SLACK_CHANNEL='#bse-announcements'
```

---

## 💬 Telegram Setup

### Step 1: Create a Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name: `BSE Announcements Bot`
4. Choose a username: `bse_announcements_bot` (must end with `bot`)
5. Copy the **Bot Token** (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

**Option A: Personal Chat**
1. Start a chat with your bot (search for your bot's username)
2. Send any message to it (e.g., `/start`)
3. Open this URL in browser (replace YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Look for `"chat":{"id":123456789` - copy that number

**Option B: Group/Channel**
1. Add your bot to the group/channel
2. Make bot an admin
3. Send a message to the group
4. Use the same URL above to get the chat ID
5. For groups, the ID will be negative (e.g., `-123456789`)

### Step 3: Set Environment Variables
```bash
export TELEGRAM_BOT_TOKEN='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
export TELEGRAM_CHAT_ID='123456789'  # or '-123456789' for groups
```

---

## 🚀 Running the App with All Integrations

### Full Command:
```bash
export OPENAI_API_KEY='sk-proj-your-key'
export SLACK_BOT_TOKEN='xoxb-your-slack-token'
export SLACK_CHANNEL='#bse-announcements'
export TELEGRAM_BOT_TOKEN='your-telegram-bot-token'
export TELEGRAM_CHAT_ID='your-chat-id'

python3 app.py
```

### Permanent Setup (Add to ~/.bashrc):
```bash
cat >> ~/.bashrc << 'EOF'
# BSE Announcements App
export OPENAI_API_KEY='sk-proj-your-key'
export SLACK_BOT_TOKEN='xoxb-your-slack-token'
export SLACK_CHANNEL='#bse-announcements'
export TELEGRAM_BOT_TOKEN='your-telegram-bot-token'
export TELEGRAM_CHAT_ID='your-chat-id'
EOF

source ~/.bashrc
```

---

## 📊 Message Format

### Slack Message:
```
🔔 Standard Shoe Sole and Mould (India) Ltd

BSE Code: 523351
Sentiment: ➖ NEUTRAL

Summary:
➖ NEUTRAL
Company: Standard Shoe Sole and Mould (India) Ltd
Analysis: Neutral

📄 View PDF on BSE
```

### Telegram Message:
```
🔔 Standard Shoe Sole and Mould (India) Ltd

BSE Code: 523351
Sentiment: ➖ NEUTRAL

Summary:
➖ NEUTRAL
Company: Standard Shoe Sole and Mould (India) Ltd
Analysis: Neutral

📄 View PDF on BSE
```

---

## ✅ Testing

1. Start the app with tokens configured
2. Open the web interface
3. Click **"Summarize"** on any announcement
4. Check console logs:
   ```
   🤖 Sending to OpenAI gpt-4o-mini for analysis...
   ✅ OpenAI Response: Neutral
   ✅ Sent to Slack channel: #bse-announcements
   ✅ Sent to Telegram chat: 123456789
   ```
5. Check your Slack channel and Telegram chat!

---

## 🔧 Troubleshooting

### Slack Issues:
- **"channel_not_found"**: Check channel name includes `#`
- **"not_authed"**: Verify your Bot Token starts with `xoxb-`
- **"missing_scope"**: Add `chat:write` and `chat:write.public` scopes

### Telegram Issues:
- **"Unauthorized"**: Check your bot token is correct
- **"Chat not found"**: Verify Chat ID (send message to bot first)
- **"Bot was blocked"**: Unblock the bot in Telegram

### No Messages Sent:
- Check environment variables are set: `echo $SLACK_BOT_TOKEN`
- Look for warning messages in console
- Messages will show: `⚠️ Slack not configured` if tokens missing

---

## 💰 Optional: Choose Which Platforms

You can configure just one platform if you want:

**Slack only:**
```bash
export SLACK_BOT_TOKEN='...'
export SLACK_CHANNEL='#bse-announcements'
# Don't set TELEGRAM variables
```

**Telegram only:**
```bash
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_CHAT_ID='...'
# Don't set SLACK variables
```

**Both:**
```bash
export SLACK_BOT_TOKEN='...'
export SLACK_CHANNEL='#bse-announcements'
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_CHAT_ID='...'
```

The app will automatically detect which platforms are configured and send to available ones!
