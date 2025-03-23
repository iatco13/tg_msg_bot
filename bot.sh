#!/bin/bash

VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
SCRIPT="bot.py"
PID_FILE=".pid"

start_bot() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Virtual environment not found. Please run setup first."
        exit 1
    fi
    
    if [ -f "$PID_FILE" ]; then
        echo "Bot is already running (PID file exists: $PID_FILE)."
        exit 1
    fi

    echo "Starting bot..."
    nohup "$PYTHON_BIN" "$SCRIPT" > bot.out 2>&1 &  # Запуск в фоновом режиме с nohup
    BOT_PID=$!  # Получаем PID последнего запущенного процесса
    echo $BOT_PID > "$PID_FILE"  # Сохраняем PID в файл
    echo "Bot started with PID $BOT_PID."
}

stop_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No PID file found. Bot may not be running."
        exit 1
    fi

    BOT_PID=$(cat "$PID_FILE")
    if ps -p "$BOT_PID" > /dev/null; then
        echo "Stopping bot (PID: $BOT_PID)..."
        kill "$BOT_PID"
        rm -f "$PID_FILE"
        echo "Bot stopped and PID file removed."
    else
        echo "Process with PID $BOT_PID not found. Removing stale PID file."
        rm -f "$PID_FILE"
    fi
}

case "$1" in
    start) start_bot ;;
    stop) stop_bot ;;
    *) echo "Usage: $0 {start|stop}" ;;
esac