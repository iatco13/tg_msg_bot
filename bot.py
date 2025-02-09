#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# Messages telegram-bot v.0.0.1 build 2502
# sends messages to all chats in the list
# license: GNU GPL v.3

"""
This module implements a Telegram bot that forwards messages to a list of chats.

The bot checks if the sender is an admin and forwards the message to all specified chats.
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TG_TOKEN, TG_DELAY, logger, tg_admins, tg_chats


def check_admin(id: int) -> bool:
    """Checks if a user is an admin.

    Args:
        id (int): The ID of the user.

    Returns:
        bool: True if the user is an admin, False otherwise.
    """
    return id in tg_admins


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming messages and forwards them to all chats in the list if the sender is an admin.

    Args:
        update (Update): The update object containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context object for the bot.
    """
    user_id = update.message.from_user.id
    
    if check_admin(user_id):
        try:
            for chat_id in tg_chats:
                await context.bot.forward_message(chat_id=chat_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
    else:
        await update.message.reply_text(f":)")


def main() -> None:
    """Starts the bot and registers the message handler."""
    application = Application.builder().token(TG_TOKEN).read_timeout(TG_DELAY).get_updates_read_timeout(TG_DELAY).write_timeout(TG_DELAY).get_updates_write_timeout(TG_DELAY).pool_timeout(TG_DELAY).get_updates_pool_timeout(TG_DELAY).connect_timeout(TG_DELAY).get_updates_connect_timeout(TG_DELAY).build()
    
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    application.run_polling()
    logger.info("Bot started.")


if __name__ == "__main__":
    main()
