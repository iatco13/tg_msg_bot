#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import json
import os
import asyncio
from config import Config
from bot import logger  # Импортируем logger из bot.py

CONFIG_PATH = "config.json"
LOG_PATH = "bot.log"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def load_logs():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            return f.readlines()
    return ["No logs available."]

def main():
    st.title("Telegram Bot Management")
    config = Config(logger)  # Передаем logger

    tab1, tab2, tab3 = st.tabs(["Settings", "Logs", "Stats"])

    with tab1:
        config_data = load_config()

        if st.button("Update Chat List"):
            updated_count = asyncio.run(config.update_chats())
            st.success(f"Chat list updated! Found {updated_count} chats.")
            st.rerun()

        st.subheader("Admins")
        admin_data = []
        for i, admin in enumerate(config_data["admins"]):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"Admin {i+1} Name", value=admin["name"], key=f"admin_name_{i}")
            with col2:
                id_val = st.text_input(f"Admin {i+1} ID", value=admin["id"], key=f"admin_id_{i}")
            admin_data.append({"name": name, "id": id_val})
        if st.button("Add Admin"):
            admin_data.append({"name": "", "id": ""})
            st.rerun()

        st.subheader("Chats")
        chat_data = []
        for i, chat in enumerate(config_data["chats"]):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                name = st.text_input(f"Chat {i+1} Name", value=chat["name"], key=f"chat_name_{i}")
            with col2:
                id_val = st.text_input(f"Chat {i+1} ID", value=chat["id"], key=f"chat_id_{i}", disabled=True)
            with col3:
                authorized = st.checkbox(f"Authorized", value=chat.get("authorized", False), key=f"chat_auth_{i}")
            chat_data.append({"name": name, "id": id_val, "authorized": authorized})
        if st.button("Add Chat"):
            chat_data.append({"name": "", "id": "", "authorized": False})
            st.rerun()

        if st.button("Save"):
            config_data["admins"] = [entry for entry in admin_data if entry["id"] and entry["name"]]
            config_data["chats"] = [entry for entry in chat_data if entry["id"] and entry["name"]]
            save_config(config_data)
            st.success("Settings saved!")

    with tab2:
        st.subheader("Bot Logs")
        logs = load_logs()
        st.text_area("Logs", value="".join(logs), height=300, disabled=True)

    with tab3:
        st.subheader("Statistics")
        logs = load_logs()
        message_count = sum(1 for log in logs if "Message forwarded to" in log)
        error_count = sum(1 for log in logs if "Error forwarding to" in log)
        st.write(f"Messages forwarded: {message_count}")
        st.write(f"Errors: {error_count}")

if __name__ == "__main__":
    main()