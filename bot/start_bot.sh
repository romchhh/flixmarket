#!/bin/bash
# Оновлено: бот у папці bot/ (раніше SubscribesBot)
# Вкажіть свій шлях до віртуального середовища та проєкту
source /root/FlixMarketBot/bot/myenv/bin/activate
nohup python3 /root/FlixMarketBot/bot/main.py > /dev/null 2>&1 &
