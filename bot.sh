#!/usr/bin/bash

start_bot() {
    # Activate the virtual environment
    source .venv/bin/activate

    # Run the bot
    python3 bot.py &
}

stop_bot() {
    # Find the process ID of bot.py and kill it
    pkill -f bot.py
}

# Check the first argument to determine whether to start or stop the bot
if [ "$1" = "start" ]; then
    start_bot
elif [ "$1" = "stop" ]; then
    stop_bot
else
    echo "Usage: $0 {start|stop}"
fi