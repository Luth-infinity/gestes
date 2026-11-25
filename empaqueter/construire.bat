@echo off
rem Construit Gestes.exe (PyInstaller) puis l'installateur (Inno Setup 6).
rem Resultat : empaqueter\sortie\Gestes-Setup-<version>.exe
cd /d "%~dp0.."
.venv\Scripts\python.exe -m pip install -q pyinstaller || goto :erreur
.venv\Scripts\python.exe empaqueter\icone.py || goto :erreur
.venv\Scripts\python.exe -m pytest -q || goto :erreur
.venv\Scripts\python.exe -m PyInstaller empaqueter\gestes.spec --noconfirm --distpath empaqueter\dist --workpath empaqueter\build || goto :erreur
set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo Inno Setup 6 introuvable : winget install JRSoftware.InnoSetup
  goto :erreur
)
"%ISCC%" /Q empaqueter\installeur.iss || goto :erreur
echo.
echo Installateur pret dans empaqueter\sortie
goto :eof
:erreur
echo Echec de la construction.
exit /b 1
