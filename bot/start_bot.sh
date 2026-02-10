#!/bin/bash
# Запуск бота з папки, де лежить скрипт (працює при будь-якому шляху до проєкту)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "./myenv/bin/activate" ]; then
  source ./myenv/bin/activate
elif [ -f "./venv/bin/activate" ]; then
  source ./venv/bin/activate
else
  echo "Не знайдено віртуальне середовище (myenv або venv) у $SCRIPT_DIR"
  exit 1
fi

nohup python3 main.py > /dev/null 2>&1 &
echo "Бот запущено (PID: $!)"
