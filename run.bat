@echo off
cd /d "%~dp0"
call venv\Scripts\activate
set DRY_RUN=0
set PYTHONUTF8=1
python main.py >> bot.log 2>&1
