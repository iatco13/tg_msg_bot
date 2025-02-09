#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module loads the configuration for the Telegram bot from environment variables.

Attributes:
    TG_TOKEN (str): The token for the Telegram bot.
    TG_DELAY (int): The delay time for the bot operations.
    TG_BOT_ID (str): The ID of the Telegram bot.
    tg_chats (list): A list of chat IDs to which messages will be forwarded.
    tg_admins (list): A list of admin user IDs.
    logger (logging.Logger): The logger instance for logging bot activities.
"""

import os
import logging
from dotenv import load_dotenv


load_dotenv()

TG_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_DELAY = 60
TG_BOT_ID = os.getenv('TG_BOT_ID')

tg_chats = [int(_s) for _s in os.getenv('TG_CHATS').split(',')]

tg_admins = [int(_s) for _s in os.getenv('TG_ADMINS').split(',')]


logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

logger = logging.getLogger(__name__)
