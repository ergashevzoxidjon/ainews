@echo off
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (echo Git o'rnatilmagan: git-scm.com dan o'rnating & pause & exit /b 1)
if not exist .git git init -b main
git check-ignore -q .env || (echo XATO: .env himoyalanmagan, to'xtatildi & pause & exit /b 1)
git add .
echo.
echo === Yuklanadigan fayllar (.env bo'lmasligi kerak) ===
git status --short
echo.
pause
git commit -m "AI yangiliklari kanali boti: birinchi versiya"
git remote remove origin >nul 2>nul
git remote add origin https://github.com/ergashevzoxidjon/ainews.git
git branch -M main
git push -u origin main
pause
