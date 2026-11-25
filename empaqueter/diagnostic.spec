# PyInstaller : construit dist/Gestes/Gestes.exe (dossier, démarrage rapide).
# Lancer via construire.bat.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

RACINE = Path(SPECPATH).parent
datas = [
    (str(RACINE / "modeles" / "hand_landmarker.task"), "modeles"),
    (str(RACINE / "gestes_webcam" / "ui"), "gestes_webcam/ui"),
]
binaries, hiddenimports = [], ["pystray._win32", "webview.platforms.edgechromium", "clr"]
for paquet in ("mediapipe",):
    d, b, h = collect_all(paquet)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    [str(RACINE / "empaqueter/diagnostic.py")],
    pathex=[str(RACINE)],
    datas=datas, binaries=binaries, hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython", "jax", "torch", "tensorflow",
              "sounddevice", "pandas", "scipy"],
    noarchive=False,
)
# La webcam passe par MSMF / DirectShow : le lecteur vidéo ffmpeg d'OpenCV (39 Mo) ne sert pas.
a.binaries = [b for b in a.binaries if "opencv_videoio_ffmpeg" not in b[0]]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="diagnostic",
    icon=str(Path(SPECPATH) / "gestes.ico"), version=str(Path(SPECPATH) / "version.txt"),
    console=True, upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="diagnostic", upx=False)
