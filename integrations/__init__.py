"""
Third-party integrations module
Contains integrations for Slack, Telegram, and Upstox
"""

from .slack_integration import send_to_slack, slack_client
from .telegram_integration import send_to_telegram, telegram_bot
from .upstox_integration import upstox_client, is_authenticated, UpstoxAPI

__all__ = [
    'send_to_slack',
    'send_to_telegram',
    'upstox_client',
    'is_authenticated',
    'UpstoxAPI',
    'slack_client',
    'telegram_bot'
]
