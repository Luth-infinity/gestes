@echo off
rem Enregistrement guide des gestes (pour regler les seuils).
cd /d "%~dp0"
.venv\Scripts\python.exe -m gestes_webcam.enregistrement
pause
