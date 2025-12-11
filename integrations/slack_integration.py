"""
Slack Integration Module
Handles sending notifications to Slack channels
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize Slack client
slack_token = os.environ.get('SLACK_BOT_TOKEN', '')
slack_channel = os.environ.get('SLACK_CHANNEL', '#bse-announcements')
slack_client = WebClient(token=slack_token) if slack_token else None


def send_to_slack(company_name, bse_code, sentiment, summary, pdf_url, announcement_time=None):
    """Send announcement summary to Slack"""
    if not slack_client:
        print("⚠️ Slack not configured (SLACK_BOT_TOKEN not set)")
        return False
    
    try:
        # Format sentiment with emoji
        sentiment_emoji = {
            'positive': '📈 POSITIVE',
            'negative': '📉 NEGATIVE',
            'neutral': '➖ NEUTRAL'
        }.get(sentiment, '❓ UNKNOWN')
        
        # Format announcement time
        time_text = f"\n*📅 Published:* {announcement_time}" if announcement_time else ""
        
        # Create concise Slack message for quick decision-making
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🏛️ {company_name}*\n*BSE:* `{bse_code}` | *Sentiment:* {sentiment_emoji}{time_text}\n<{pdf_url}|📄 View PDF>"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        response = slack_client.chat_postMessage(
            channel=slack_channel,
            blocks=blocks,
            text=f"{company_name} - {sentiment_emoji}"  # Fallback text
        )
        
        if response['ok']:
            print(f"✅ Sent to Slack channel: {slack_channel}")
            print(f"   Message timestamp: {response['ts']}")
            return True
        else:
            print(f"❌ Slack response not OK: {response}")
            return False
        
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Error sending to Slack: {str(e)}")
        return False
