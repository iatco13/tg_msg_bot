# Telegram Message Bot

This project implements a Telegram bot that forwards messages to a list of specified chats. The bot checks if the sender is an admin and forwards the message to all specified chats.

## Features

- Forwards messages to a list of chats
- Checks if the sender is an admin
- Logs bot activities

## Requirements

- Python 3.7+
- `python-telegram-bot` library
- `python-dotenv` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/iatco13/tg_msg_bot.git
    cd tg_msg_bot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a [.env](http://_vscodecontentref_/0) file and add your Telegram bot token, bot ID, chat IDs, and admin IDs:
    ```env
    TG_BOT_TOKEN=your_bot_token
    TG_BOT_ID=your_bot_id
    TG_CHATS=chat_id1,chat_id2
    TG_ADMINS=admin_id1,admin_id2
    ```

## Usage

To start the bot, run:
```sh
./bot.sh start