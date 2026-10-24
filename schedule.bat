@echo off
rem Har 90 daqiqada run.bat ni avtomatik ishga tushiradi (Windows Task Scheduler)
schtasks /Create /SC MINUTE /MO 90 /TN "AI_Yangiliklar_Bot" /TR "\"%~dp0run.bat\"" /F
pause
