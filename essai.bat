@echo off
rem Mode diagnostic : fenetre video, journal CSV, aucune action executee.
cd /d "%~dp0"
.venv\Scripts\python.exe -m gestes_webcam --essai --journal
