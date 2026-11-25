@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Installation de l'environnement...
  py -3.12 -m venv .venv || goto :erreur
  .venv\Scripts\python.exe -m pip install -r requirements.txt || goto :erreur
)
start "" .venv\Scripts\pythonw.exe gestes.pyw %*
goto :eof
:erreur
echo Echec de l'installation. Python 3.12 est-il installe ?
pause
