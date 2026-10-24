@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .env copy .env.example .env
python -m venv venv || (echo Python o'rnatilmagan: python.org dan o'rnating & pause & exit /b 1)
call venv\Scripts\activate
pip install -r requirements.txt
python check.py
echo.
echo Sinov (hech narsa yuborilmaydi): DRY_RUN=1
set DRY_RUN=1
python main.py
pause
