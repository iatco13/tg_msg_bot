#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# Messages telegram-bot v.0.0.3 build 2504
# Sends messages to all chats in the list
# License: GNU GPL v.3


"""Telegram Message Forwarding Bot.

This bot forwards messages from authorized admins to multiple Telegram groups.
It supports webhook and polling methods, with comprehensive logging and group management.

The main components are:
- FastAPI webhook handler
- Telegram bot application
- Configuration manager
- Group discovery system

Example:
    To run the bot:
    $ ./bot.sh start

Attributes:
    TG_DELAY (float): Timeout for Telegram API operations.
    logger (Logger): Configured logger instance for the application.
"""


import logging
import os.path
import sys
import asyncio
import uvicorn
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext, ChatMemberHandler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config


# Logging setup
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# FastAPI app initialization
app = FastAPI()


# Configuration and Telegram application setup
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


# Async lifecycle management for the bot
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the Telegram bot application."""
    await initialize_application()
    logger.info("Bot initialized and webhook set")
    yield
    await application.stop()
    logger.info("Bot stopped")


app = FastAPI(lifespan=lifespan)


# Message forwarding handler
async def handle_forward_message(update: Update, context: CallbackContext) -> None:
    logger.info(f"Processing message: {update.message}")
    config.load_dynamic_config()
    sender_id = update.effective_user.id
    sender_id_str = str(sender_id)

    admin_ids = config.get_admin_ids()
    if sender_id_str not in admin_ids:
        #logger.info(f"User {sender_id} is not an admin")
        #await update.message.reply_text("You are not an admin!")
        return

    authorized_chat_ids: List[str] = config.get_authorized_chat_ids()  # This now only returns chats with authorized=True

    tasks = []
    for chat_id in authorized_chat_ids:
        tasks.append(send_message_with_logging(chat_id, update, context))

    if not tasks:
        logger.info("No authorized chats to forward the message to")
        await update.message.reply_text("No authorized chats available to forward the message.")
        return

    await asyncio.gather(*tasks)


async def send_message_with_logging(chat_id: str, update: Update, context: CallbackContext):
    try:
        await context.bot.forward_message(chat_id=chat_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        chat_name = next((chat["name"] for chat in config.chats if chat["id"] == chat_id), chat_id)
        logger.info(f"Message forwarded to {chat_name} ({chat_id})")
    except Exception as e:
        logger.error(f"Error forwarding to {chat_id}: {e}")


# Chat member handler
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


# Error handler
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")


# Webhook setup
async def set_webhook() -> bool:
    """Asynchronously set the webhook for the bot."""
    if not config.webhook_url:
        logger.error("WEBHOOK_URL is not set in .env")
        return False

    if config.cert_pem and config.cert_key:
        try:
            with open(config.cert_pem, "rb") as cert_file:
                result = await application.bot.set_webhook(
                    url=config.webhook_url,
                    #certificate=cert_file
                )
            logger.info("Webhook set with custom certificate")
            return result
        except Exception as e:
            logger.error(f"Failed to set webhook with certificate: {e}")
            return False
    else:
        result = await application.bot.set_webhook(url=config.webhook_url)
        logger.info("Webhook set without certificate")
        return result


# Group discovery at startup
async def discover_groups_at_startup():
    logger.info("Discovering groups at startup...")
    discovered_chats = set()

    try:
        current_chats = config.get_chat_ids()
        for chat_id in current_chats:
            try:
                chat_member = await application.bot.get_chat_member(chat_id, application.bot.id)
                if chat_member.status in ["member", "administrator"]:
                    chat = await application.bot.get_chat(chat_id)
                    if chat.type in ["group", "supergroup"]:
                        discovered_chats.add((str(chat.id), chat.title or f"Chat {chat.id}", True))
                        logger.info(f"Confirmed group from config: {chat.title} ({chat.id})")
                else:
                    discovered_chats.add((str(chat.id), chat.title or f"Chat {chat.id}", False))
                    logger.info(f"Bot is no longer in {chat_id}")
            except Exception as e:
                logger.info(f"Chat {chat_id} inaccessible: {e}")

        config.chats = [{"id": chat_id, "name": chat_name, "authorized": chat_authorized} for chat_id, chat_name, chat_authorized in discovered_chats]
        config.save_config()
        logger.info(f"Discovered and confirmed {len(config.chats)} groups, updated config.json")
    except Exception as e:
        logger.error(f"Error during group discovery: {e}")


# Application initialization
async def initialize_application():
    await application.initialize()
    logger.info("Application initialized")
    
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook disabled temporarily for group discovery")

    await discover_groups_at_startup()

    if await set_webhook():
        logger.info("Webhook set successfully")
    else:
        logger.error("Failed to set webhook")


# Add handlers
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_forward_message))
application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
application.add_error_handler(error_handler)


# Webhook endpoint
@app.post("/webhook")
async def process_update(request: Request):
    """Handle incoming Telegram updates via webhook."""
    logger.info("Webhook request received")
    try:
        req = await request.json()
        logger.info(f"Raw update data: {req}")
        update = Update.de_json(req, application.bot)
        if update:
            logger.info(f"Parsed update: {update}")
            await application.process_update(update)
            logger.info("Update processed successfully")
            return Response(status_code=200)
        else:
            logger.error("Failed to parse update from JSON")
            return Response(status_code=400)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return Response(status_code=500)


@app.get("/webhook")
async def index():
    """Basic health check endpoint."""
    logger.info("Health check endpoint accessed")
    return {"message": "Telegram Bot Webhook is running!"}


if __name__ == "__main__":
    # Run the FastAPI app with SSL for webhook
    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile=config.cert_key,
        ssl_certfile=config.cert_pem,
        log_level="info"
    )
