#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# Messages telegram-bot v.0.0.2 build 2503
# sends messages to all chats in the list
# license: GNU GPL v.3


import logging
import os.path
import sys
import asyncio
from flask import Flask, request
from typing import List

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext, ChatMemberHandler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config


logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

config = Config(logger)

TG_DELAY = float(os.getenv("TG_DELAY", 120))

application = (
    Application.builder()
    .token(config.token)
    .read_timeout(TG_DELAY)
    .get_updates_read_timeout(TG_DELAY)
    .write_timeout(TG_DELAY)
    .get_updates_write_timeout(TG_DELAY)
    .pool_timeout(TG_DELAY)
    .get_updates_pool_timeout(TG_DELAY)
    .connect_timeout(TG_DELAY)
    .get_updates_connect_timeout(TG_DELAY)
    .connection_pool_size(20)
    .build()
)


async def forward_message(update: Update, context: CallbackContext) -> None:
    logger.info(f"Processing message: {update.message.text}")
    config.load_dynamic_config()
    sender_id = update.effective_user.id
    sender_id_str = str(sender_id)

    admin_ids = config.get_admin_ids()
    if sender_id_str not in admin_ids:
        logger.info(f"User {sender_id} is not an admin")
        await update.message.reply_text("You are not an admin!")
        return

    message_text = update.message.text
    authorized_chat_ids: List[str] = config.get_authorized_chat_ids()
    
    tasks = []
    for chat_id in authorized_chat_ids:
        tasks.append(send_message_with_logging(chat_id, message_text))
    
    await asyncio.gather(*tasks)


async def send_message_with_logging(chat_id: str, message_text: str):
    try:
        await application.bot.send_message(chat_id=chat_id, text=message_text)
        chat_name = next((chat["name"] for chat in config.chats if chat["id"] == chat_id), chat_id)
        logger.info(f"Message forwarded to {chat_name} ({chat_id})")
    except Exception as e:
        logger.error(f"Error forwarding to {chat_id}: {e}")


async def handle_chat_member(update: Update, context: CallbackContext) -> None:
    logger.info(f"Processing chat member update: {update.my_chat_member}")
    chat = update.my_chat_member.chat
    if chat.type not in ["group", "supergroup"]:
        return

    new_status = update.my_chat_member.new_chat_member.status
    chat_id = str(chat.id)
    chat_name = chat.title or f"Chat {chat_id}"

    if new_status == "member":
        logger.info(f"Bot added to {chat_name} ({chat_id})")
    elif new_status in ["kicked", "left"]:
        logger.info(f"Bot removed from {chat_name} ({chat_id})")

    try:
        await config.update_chats(update)
        logger.info("Chat list updated due to membership change")
    except Exception as e:
        logger.error(f"Failed to update chats: {e}")


async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")


async def set_webhook() -> bool:
    """Асинхронно устанавливает webhook для бота."""
    if not config.webhook_url:
        logger.error("WEBHOOK_URL is not set in .env")
        return False
        
    if config.cert_pem and config.cert_key:
        try:
            with open(config.cert_pem, "rb") as cert_file:
                result = await application.bot.set_webhook(
                    url=config.webhook_url,
                    #certificate=cert_file,
                    allowed_updates=["message", "my_chat_member"]  # Указываем нужные типы обновлений
                )
            logger.info("Webhook set with custom certificate")
            return result
        except Exception as e:
            logger.error(f"Failed to set webhook with certificate: {e}")
            return False
    else:
        result = await application.bot.set_webhook(url=config.webhook_url)
        return result
        

application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
application.add_error_handler(error_handler)


@app.route('/webhook', methods=['POST', 'GET'])
async def webhook():
    if request.method == 'POST':
        json_data = request.get_json(force=True)
        logger.info(f"Received update: {json_data}")
        update = Update.de_json(json_data, application.bot)
        if update:
            logger.info(f"Parsed update: {update}")
            await application.process_update(update)
        else:
            logger.error("Failed to parse update from JSON")
        return "OK", 200
    return "Webhook is running", 200


@app.route('/')
def index():
    return "Telegram Bot Webhook is running!"


async def initialize_application():
    await application.initialize()
    logger.info("Application initialized")

    if await set_webhook():
        logger.info(f"Webhook set to {config.webhook_url}")
    else:
        logger.error("Failed to set webhook. Check WEBHOOK_URL in .env")
        return


def main():
    asyncio.run(initialize_application())

    if config.cert_pem and config.cert_key:
        logger.info(f"Starting Flask with SSL: {config.cert_pem}, {config.cert_key}")
        app.run(host="0.0.0.0", port=8443, ssl_context=(config.cert_pem, config.cert_key))
    else:
        logger.info("Starting Flask without SSL (use Ngrok for HTTPS)")
        app.run(host="0.0.0.0", port=8443)

if __name__ == "__main__":
    main()