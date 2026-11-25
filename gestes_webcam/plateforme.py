"""Ce qui change entre Windows et macOS : thème, démarrage automatique, instance unique,
application au premier plan, curseur, touches média, raccourci global.

Le reste de l'app ne parle qu'à ce module. Sur macOS, tout passe par PyObjC (installé avec
pywebview) ; l'app doit avoir les autorisations Caméra et Accessibilité.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MAC = sys.platform == "darwin"
WINDOWS = sys.platform == "win32"
NOM_PLATEFORME = "mac" if MAC else "windows"

# Touches de l'interface -> PyAutoGUI. « win » devient Commande sur Mac.
TOUCHE_SYSTEME = "command" if MAC else "win"
TOUCHE_FENETRES = "command" if MAC else "alt"      # tenue pendant le sélecteur de fenêtres

# Raccourcis système : action -> touches (pour les directions : (droite, gauche))
if MAC:
    RACCOURCIS = {
        "capture": ("command", "shift", "5"), "vue_taches": ("ctrl", "up"), "afficher_bureau": ("command", "f3"),
        "bureau_virtuel": (("ctrl", "right"), ("ctrl", "left")),
        "fenetre": (("command", "tab"), ("command", "shift", "tab")),
        "choisir_fenetre": ("ctrl", "up"),          # Mission Control
    }
else:
    RACCOURCIS = {
        "capture": ("win", "shift", "s"), "vue_taches": ("win", "tab"), "afficher_bureau": ("win", "d"),
        "bureau_virtuel": (("ctrl", "win", "right"), ("ctrl", "win", "left")),
        "fenetre": (("alt", "tab"), ("alt", "shift", "tab")),
        "choisir_fenetre": ("win", "tab"),
    }


# --------------------------------------------------------------------------- dossiers
def dossier_reglages() -> Path:
    if MAC:
        return Path.home() / "Library" / "Application Support" / "Gestes"
    return Path(os.environ.get("APPDATA", Path.home())) / "Gestes"


def dossier_donnees() -> Path:
    if MAC:
        return Path.home() / "Library" / "Application Support" / "Gestes"
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Gestes"


# --------------------------------------------------------------------------- système
def theme_sombre() -> bool:
    try:
        if MAC:
            r = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True)
            return "dark" in r.stdout.lower()
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
    except Exception:
        return False


AGENT_MAC = Path.home() / "Library" / "LaunchAgents" / "fr.luth.gestes.plist"


def demarrage_auto(actif: bool, arguments: list[str]) -> None:
    """Lance l'app à l'ouverture de session (`arguments` : la commande complète)."""
    if MAC:
        if actif:
            import plistlib
            AGENT_MAC.parent.mkdir(parents=True, exist_ok=True)
            with open(AGENT_MAC, "wb") as f:
                plistlib.dump({"Label": "fr.luth.gestes", "ProgramArguments": arguments, "RunAtLoad": True}, f)
        else:
            AGENT_MAC.unlink(missing_ok=True)
        return
    import winreg
    cle = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cle, 0, winreg.KEY_SET_VALUE) as k:
        if actif:
            winreg.SetValueEx(k, "Gestes", 0, winreg.REG_SZ, " ".join(f'"{a}"' if " " in a else a for a in arguments))
        else:
            try:
                winreg.DeleteValue(k, "Gestes")
            except FileNotFoundError:
                pass


_verrou = None


def une_seule_instance() -> bool:
    global _verrou
    if MAC:
        import fcntl
        d = dossier_donnees()
        d.mkdir(parents=True, exist_ok=True)
        _verrou = open(d / ".instance", "w")
        try:
            fcntl.flock(_verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False
    import ctypes
    _verrou = ctypes.windll.kernel32.CreateMutexW(None, False, "Gestes.Webcam.Instance")
    return ctypes.windll.kernel32.GetLastError() != 183   # ERROR_ALREADY_EXISTS


def alerte(message: str) -> None:
    if MAC:
        texte = message.replace('"', '\\"')
        subprocess.run(["osascript", "-e", f'display dialog "{texte}" with title "Gestes" buttons {{"OK"}}'])
        return
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, message, "Gestes", 0x40)


def ouvrir_fichier(chemin: str) -> None:
    if MAC:
        subprocess.Popen(["open", chemin])
    else:
        os.startfile(chemin)


# --------------------------------------------------------------------------- caméra
def backends_camera() -> tuple[int, ...]:
    import cv2
    if MAC:
        return (cv2.CAP_AVFOUNDATION,)
    return (cv2.CAP_MSMF, cv2.CAP_DSHOW)


def backend_liste_cameras() -> int:
    import cv2
    return cv2.CAP_AVFOUNDATION if MAC else cv2.CAP_DSHOW


# --------------------------------------------------------------------------- premier plan
def appli_au_premier_plan() -> tuple[str, str]:
    """(nom de l'exécutable en minuscules, titre). Sur Mac, le titre est le nom de l'app :
    lire le titre des fenêtres demanderait l'autorisation d'enregistrement d'écran."""
    try:
        if MAC:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is None:
                return "", ""
            url = app.executableURL()
            exe = (url.lastPathComponent() if url else app.localizedName() or "").lower()
            return exe, app.localizedName() or ""
        import ctypes
        from ctypes import wintypes
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        hwnd = u32.GetForegroundWindow()
        titre = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(hwnd, titre, 512)
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = k32.OpenProcess(0x1000, False, pid.value)   # PROCESS_QUERY_LIMITED_INFORMATION
        chemin = ctypes.create_unicode_buffer(1024)
        taille = wintypes.DWORD(1024)
        exe = ""
        if h:
            if k32.QueryFullProcessImageNameW(h, 0, chemin, ctypes.byref(taille)):
                exe = os.path.basename(chemin.value).lower()
            k32.CloseHandle(h)
        return exe, titre.value
    except Exception:
        return "", ""


# --------------------------------------------------------------------------- curseur
def position_curseur() -> tuple[float, float] | None:
    try:
        if MAC:
            import Quartz
            p = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
            return float(p.x), float(p.y)
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT()
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            return float(pt.x), float(pt.y)
    except Exception:
        pass
    return None


def placer_curseur(x: int, y: int) -> None:
    if MAC:
        import Quartz
        ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
        return
    import ctypes
    ctypes.windll.user32.SetCursorPos(x, y)


# --------------------------------------------------------------------------- touches média
TOUCHES_MEDIA_MAC = {"playpause": "KEYTYPE_PLAY", "nexttrack": "KEYTYPE_NEXT", "prevtrack": "KEYTYPE_PREVIOUS",
                     "volumeup": "KEYTYPE_SOUND_UP", "volumedown": "KEYTYPE_SOUND_DOWN", "volumemute": "KEYTYPE_MUTE"}


def touche_media(pg, nom: str, fois: int = 1) -> bool:
    """Envoie une touche média. Renvoie False si ce n'en est pas une (à envoyer normalement)."""
    if not MAC or nom not in TOUCHES_MEDIA_MAC:
        if nom in TOUCHES_MEDIA_MAC:
            pg.press(nom, presses=fois)
            return True
        return False
    from pyautogui import _pyautogui_osx as osx
    for _ in range(fois):
        osx._specialKeyEvent(TOUCHES_MEDIA_MAC[nom], "down")
        osx._specialKeyEvent(TOUCHES_MEDIA_MAC[nom], "up")
    return True


# --------------------------------------------------------------------------- raccourci global
def ecouter_raccourci(rappel) -> None:
    """Ctrl + Alt + G (Ctrl + Option + G sur Mac), partout. Bloque : à lancer dans un fil."""
    if MAC:
        try:
            from pynput import keyboard
        except ImportError:
            return
        with keyboard.GlobalHotKeys({"<ctrl>+<alt>+g": rappel}) as h:
            h.join()
        return
    import ctypes
    from ctypes import wintypes
    u32 = ctypes.windll.user32
    MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, WM_HOTKEY = 0x1, 0x2, 0x4000, 0x0312
    if not u32.RegisterHotKey(None, 1, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, ord("G")):
        return   # déjà pris par une autre app : l'interrupteur reste disponible
    msg = wintypes.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            rappel()
