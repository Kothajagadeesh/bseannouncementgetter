"""
Telegram Integration Module
Handles sending notifications to Telegram channels/groups
"""

import os
import asyncio
import telegram
from telegram.error import TelegramError

# Initialize Telegram bot
telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
telegram_bot = telegram.Bot(token=telegram_token) if telegram_token else None


def send_to_telegram(company_name, bse_code, sentiment, summary, pdf_url):
    """Send announcement summary to Telegram"""
    if not telegram_bot or not telegram_chat_id:
        print("⚠️ Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set)")
        return False
    
    try:
        # Format sentiment with emoji
        sentiment_emoji = {
            'positive': '📈 POSITIVE',
            'negative': '📉 NEGATIVE',
            'neutral': '➖ NEUTRAL'
        }.get(sentiment, '❓ UNKNOWN')
        
        # Create formatted message
        message = f"""🔔 *{company_name}*

*BSE Code:* `{bse_code}`
*Sentiment:* {sentiment_emoji}

*Summary:*
{summary}

[📄 View PDF on BSE]({pdf_url})"""
        
        # Send message using async run in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            telegram_bot.send_message(
                chat_id=telegram_chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        )
        loop.close()
        
        print(f"✅ Sent to Telegram chat: {telegram_chat_id}")
        return True
        
    except TelegramError as e:
        print(f"❌ Telegram Error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False
