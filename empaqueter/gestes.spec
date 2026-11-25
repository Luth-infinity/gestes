# PyInstaller : construit Gestes (dossier) sur Windows, Gestes.app sur macOS.
# Lancer via construire.bat (Windows) ou le workflow GitHub « Release ».
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

MAC = sys.platform == "darwin"
ICI = Path(SPECPATH)
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
from gestes_webcam import __version__ as VERSION  # noqa: E402

datas = [
    (str(RACINE / "modeles" / "hand_landmarker.task"), "modeles"),
    (str(RACINE / "gestes_webcam" / "ui"), "gestes_webcam/ui"),
]
binaries = []
if MAC:
    hiddenimports = ["pystray._darwin", "webview.platforms.cocoa", "pynput.keyboard._darwin", "pynput.mouse._darwin"]
else:
    hiddenimports = ["pystray._win32", "webview.platforms.edgechromium", "clr"]
for paquet in ("mediapipe",):
    d, b, h = collect_all(paquet)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    [str(RACINE / "gestes.pyw")],
    pathex=[str(RACINE)],
    datas=datas, binaries=binaries, hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython", "jax", "torch", "tensorflow",
              "sounddevice", "pandas", "scipy"],
    noarchive=False,
)
# La webcam passe par MSMF / DirectShow / AVFoundation : le lecteur vidéo ffmpeg d'OpenCV (39 Mo) ne sert pas.
a.binaries = [b for b in a.binaries if "opencv_videoio_ffmpeg" not in b[0]]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Gestes",
    icon=str(ICI / ("gestes.icns" if MAC else "gestes.ico")),
    version=None if MAC else str(ICI / "version.txt"),
    console=False, upx=False, argv_emulation=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Gestes", upx=False)

if MAC:
    app = BUNDLE(
        coll, name="Gestes.app", icon=str(ICI / "gestes.icns"), bundle_identifier="fr.luth.gestes",
        version=VERSION,
        info_plist={
            "CFBundleName": "Gestes",
            "CFBundleDisplayName": "Gestes",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
            "NSCameraUsageDescription": "Gestes regarde ta main pour reconnaître les gestes. Les images restent sur ton Mac.",
            "NSAppleEventsUsageDescription": "Gestes envoie les raccourcis des gestes à l'app au premier plan.",
        },
    )
