#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Configuration management for the Telegram bot.

This module handles all configuration aspects including:
- Environment variables
- Dynamic chat and admin management
- Configuration persistence

Attributes:
    token (str): Telegram bot token
    bot_id (str): Bot's numeric ID
    webhook_url (str): Webhook URL for Telegram API
    cert_pem (str): Path to SSL certificate
    cert_key (str): Path to SSL private key
    admins (list): List of admin users
    chats (list): List of authorized chats
"""


import os
import json
from dotenv import load_dotenv


class Config:
    def __init__(self, logger) -> None:
        load_dotenv()
        self.token: str = os.getenv("TG_BOT_TOKEN")
        self.bot_id: str = os.getenv("TG_BOT_ID")
        self.webhook_url: str = os.getenv("WEBHOOK_URL")
        self.cert_pem: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.getenv("CERT_PEM"))) if os.getenv("CERT_PEM") else None
        self.cert_key: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.getenv("CERT_KEY"))) if os.getenv("CERT_KEY") else None
        self.logger = logger
        self.load_dynamic_config()

    def load_dynamic_config(self) -> None:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            self.admins = config.get("admins", [])
            self.chats = config.get("chats", [])
            # Ensure all chats have an "authorized" field, default to True if missing
            for chat in self.chats:
                if "authorized" not in chat:
                    chat["authorized"] = True
        except FileNotFoundError:
            self.admins = []
            self.chats = []
            self.save_config()

    def save_config(self) -> None:
        """Сохраняет текущую конфигурацию в config.json."""
        config = {
            "admins": self.admins,
            "chats": self.chats
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    def get_admin_ids(self) -> list:
        return [admin["id"] for admin in self.admins]

    def get_authorized_chat_ids(self) -> list:
        # Only return chat IDs where authorized is True
        return [chat["id"] for chat in self.chats if chat.get("authorized", True)]
    
    def get_chat_ids(self) -> list:
        # Returns all chat IDs
        return [chat["id"] for chat in self.chats]

    async def update_chats(self, update=None) -> int:
        """Обновляет список чатов в зависимости от статуса бота в группе."""
        if not update or not update.my_chat_member:
            return len(self.chats)

        chat = update.my_chat_member.chat
        if chat.type not in ["group", "supergroup"]:
            return len(self.chats)

        chat_id = str(chat.id)
        chat_name = chat.title or f"Chat {chat_id}"
        new_status = update.my_chat_member.new_chat_member.status

        # Загружаем текущий список чатов
        existing_chats = {chat["id"]: chat for chat in self.chats}

        if new_status == "member":
            # Бот добавлен в группу
            if chat_id not in existing_chats:
                self.logger.info(f"Adding chat {chat_name} ({chat_id}) to config")
                existing_chats[chat_id] = {
                    "name": chat_name,
                    "id": chat_id,
                    "authorized": True  # New chats are authorized by default
                }
            else:
                # If the chat already exists, ensure it's authorized
                existing_chats[chat_id]["authorized"] = True
                self.logger.info(f"Chat {chat_name} ({chat_id}) re-authorized")
        elif new_status in ["kicked", "left"]:
            # Бот удален из группы
            if chat_id in existing_chats:
                self.logger.info(f"Marking chat {chat_name} ({chat_id}) as unauthorized")
                existing_chats[chat_id]["authorized"] = False  # Set authorized to False instead of removing

        # Обновляем список чатов и сохраняем
        self.chats = list(existing_chats.values())
        self.save_config()
        self.load_dynamic_config()
        return len(self.chats)
