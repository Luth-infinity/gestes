"""L'application : fenêtre de réglages, icône près de l'horloge (barre des menus sur Mac),
raccourci global, témoin flottant.

Lancement : `pythonw gestes.pyw` (ou `--cache` pour démarrer dans la zone de notification).
"""
from __future__ import annotations

import ctypes
import sys
import threading
import time

import webview

from . import plateforme as pf
from . import reglages as reg
from .catalogue import ACTIONS, GESTES
from .chemins import UI, commande_demarrage
from .service import Service

TITRE_TEMOIN = "Gestes - temoin"
if pf.WINDOWS:
    from ctypes import wintypes
    u32 = ctypes.windll.user32
    # « Toujours au premier plan » : doit être passé comme un vrai HWND. Un simple -1 arrive
    # tronqué sur Windows 64 bits, et SetWindowPos échoue sans bruit (erreur 1400).
    HWND_TOPMOST = wintypes.HWND(-1)

theme_sombre = pf.theme_sombre


def demarrage_windows(actif: bool) -> None:
    """Lancement à l'ouverture de session (clé Run sur Windows, LaunchAgent sur macOS)."""
    pf.demarrage_auto(actif, commande_demarrage())


def lister_cameras(occupee: int) -> list[dict]:
    """Essaie les 4 premières caméras. Celle déjà ouverte par l'app est toujours listée."""
    import cv2
    cams = []
    for i in range(4):
        if i == occupee:
            cams.append({"index": i, "nom": f"Caméra {i + 1}" + (" (par défaut)" if i == 0 else "")})
            continue
        c = cv2.VideoCapture(i, pf.backend_liste_cameras())
        if c.isOpened():
            cams.append({"index": i, "nom": f"Caméra {i + 1}" + (" (par défaut)" if i == 0 else "")})
        c.release()
    return cams


# --------------------------------------------------------------------------- témoin
class TemoinWindows:
    """Petite pastille flottante. Toujours affichée mais transparente : elle n'active
    jamais de fenêtre (indispensable pendant le sélecteur Alt+Tab) et laisse passer les clics."""

    L, H = 300, 48

    def __init__(self) -> None:
        self.fenetre = None
        self.hwnd = 0
        self._gen = 0

    def creer(self) -> None:
        self.fenetre = webview.create_window(
            TITRE_TEMOIN, str(UI / "temoin.html"), width=self.L, height=self.H, x=-4000, y=-4000,
            min_size=(self.L, self.H),   # sinon pywebview impose 200 x 100 : la pastille devient un pavé
            frameless=True, on_top=True, focus=False, resizable=False, background_color="#2a2c31")
        self.fenetre.events.shown += self._preparer

    def _preparer(self) -> None:
        for _ in range(50):
            self.hwnd = u32.FindWindowW(None, TITRE_TEMOIN)
            if self.hwnd:
                break
            time.sleep(0.05)
        if not self.hwnd:
            return
        GWL_EXSTYLE = -20
        style = u32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        style = (style | 0x80000 | 0x20 | 0x80 | 0x8000000) & ~0x40000   # layered, transparent, tool, noactivate
        u32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, style)
        u32.SetLayeredWindowAttributes(self.hwnd, 0, 0, 2)
        try:   # coins arrondis de Windows 11, comme ses propres notifications
            arrondi = ctypes.c_int(2)   # DWMWCP_ROUND
            ctypes.windll.dwmapi.DwmSetWindowAttribute(self.hwnd, 33, ctypes.byref(arrondi), 4)
        except Exception:
            pass
        self._placer()

    def _placer(self) -> None:
        """En bas à droite de la zone de travail, au-dessus de la barre des tâches.
        Refait à chaque affichage : pywebview peut remettre la fenêtre à sa position de
        création (hors écran), et la taille doit suivre le zoom de l'écran."""
        try:
            echelle = u32.GetDpiForWindow(self.hwnd) / 96 or 1.0
        except Exception:
            echelle = 1.0
        # La fenêtre peut garder une taille imposée par pywebview : on part de sa taille réelle.
        x0, y0, x1, y1 = self.position()
        w, h = x1 - x0, y1 - y0
        haut = min(h, int(self.H * echelle))        # hauteur de la pastille, centrée dans la fenêtre
        zone = wintypes.RECT()
        u32.SystemParametersInfoW(0x30, 0, ctypes.byref(zone), 0)
        marge = int(16 * echelle)
        x, y = zone.right - w - marge, zone.bottom - marge - haut - (h - haut) // 2
        # 0x0001 taille inchangée ; 0x0010 sans activer ; 0x0040 montrer
        u32.SetWindowPos(self.hwnd, HWND_TOPMOST, x, y, 0, 0, 0x0001 | 0x0010 | 0x0040)

    def position(self) -> tuple[int, int, int, int]:
        r = wintypes.RECT()
        u32.GetWindowRect(self.hwnd, ctypes.byref(r))
        return r.left, r.top, r.right, r.bottom

    def montrer(self, libelle: str, icone: str, geste: str = "", ton: str = "") -> None:
        """`ton` : "" (action, vert), "arme" (gestes armés) ou "veille" (gestes désarmés)."""
        if not self.hwnd or not self.fenetre:
            return
        import json
        self.fenetre.evaluate_js(
            f"montrer({json.dumps(libelle)}, {json.dumps(icone)}, {json.dumps(geste)}, {json.dumps(ton)})")
        self._gen += 1
        duree = 2.4 if ton else 1.4      # changement d'état : affiché un peu plus longtemps
        threading.Thread(target=self._animer, args=(self._gen, duree), daemon=True).start()

    def _animer(self, gen: int, duree: float = 1.4) -> None:
        alpha = lambda a: u32.SetLayeredWindowAttributes(self.hwnd, 0, int(a), 2)
        self._placer()
        for i in range(1, 7):
            if gen != self._gen:
                return
            alpha(240 * i / 6)
            time.sleep(0.016)
        time.sleep(duree)
        for i in range(6, -1, -1):
            if gen != self._gen:
                return
            alpha(240 * i / 6)
            time.sleep(0.025)


class TemoinMac:
    """La même pastille sur macOS : fenêtre au niveau des barres d'état, qui ignore la souris,
    présente sur tous les bureaux, jamais activée. Les appels AppKit passent par le fil principal."""

    L, H = 300, 48
    NIVEAU = 25            # NSStatusWindowLevel
    COMPORTEMENT = (1 << 0) | (1 << 4) | (1 << 8)   # tous les bureaux, immobile, plein écran

    def __init__(self) -> None:
        self.fenetre = None
        self.hwnd = 0      # 1 quand la fenêtre native est prête
        self._ns = None
        self._gen = 0

    def creer(self) -> None:
        self.fenetre = webview.create_window(
            TITRE_TEMOIN, str(UI / "temoin.html"), width=self.L, height=self.H, min_size=(self.L, self.H),
            frameless=True, on_top=True, focus=False, resizable=False, hidden=True,
            background_color="#2a2c31")
        self.fenetre.events.loaded += lambda: self._principal(self._preparer)

    @staticmethod
    def _principal(fn, *args) -> None:
        from PyObjCTools import AppHelper
        AppHelper.callAfter(fn, *args)

    def _preparer(self) -> None:
        try:
            from AppKit import NSApplication
            ns = next((w for w in NSApplication.sharedApplication().windows() if w.title() == TITRE_TEMOIN), None)
            if ns is None:
                return
            ns.setIgnoresMouseEvents_(True)
            ns.setLevel_(self.NIVEAU)
            ns.setCollectionBehavior_(self.COMPORTEMENT)
            ns.setAlphaValue_(0.0)
            self._ns = ns
            self._placer()
            ns.orderFrontRegardless()
            self.hwnd = 1
        except Exception:
            self._ns = None

    def _placer(self) -> None:
        """En bas à droite de l'écran principal, au-dessus du Dock."""
        from AppKit import NSScreen
        zone = NSScreen.mainScreen().visibleFrame()
        cadre = self._ns.frame()
        x = zone.origin.x + zone.size.width - cadre.size.width - 16
        y = zone.origin.y + 16
        self._ns.setFrameOrigin_((x, y))

    def montrer(self, libelle: str, icone: str, geste: str = "", ton: str = "") -> None:
        if not self.hwnd or not self.fenetre:
            return
        import json
        self.fenetre.evaluate_js(
            f"montrer({json.dumps(libelle)}, {json.dumps(icone)}, {json.dumps(geste)}, {json.dumps(ton)})")
        self._gen += 1
        duree = 2.4 if ton else 1.4
        threading.Thread(target=self._animer, args=(self._gen, duree), daemon=True).start()

    def _alpha(self, a: float) -> None:
        if self._ns is not None:
            self._principal(self._ns.setAlphaValue_, a)

    def _animer(self, gen: int, duree: float = 1.4) -> None:
        self._principal(self._placer)
        self._principal(self._ns.orderFrontRegardless)
        for i in range(1, 7):
            if gen != self._gen:
                return
            self._alpha(0.94 * i / 6)
            time.sleep(0.016)
        time.sleep(duree)
        for i in range(6, -1, -1):
            if gen != self._gen:
                return
            self._alpha(0.94 * i / 6)
            time.sleep(0.025)


Temoin = TemoinMac if pf.MAC else TemoinWindows


# --------------------------------------------------------------------------- appli
class Appli:
    def __init__(self, cache: bool = False, essai: bool = False) -> None:
        self.r = reg.charger()
        reg.appliquer(self.r)
        self.cache = cache
        self.cameras: list[dict] = []
        self.temoin = Temoin()
        self.service = Service(self.r, sur_action=self._sur_action, essai=essai)
        self.fenetre = None
        self.icone = None
        self.quitter_demande = False

    # --- actions ---
    def basculer(self, on: bool | None = None) -> bool:
        on = (not self.r["ecoute"]) if on is None else bool(on)
        self.r["ecoute"] = on
        reg.enregistrer(self.r)
        if on:
            self.service.demarrer()
        else:
            self.service.arreter()
        self._maj_icone()
        if self.r["temoin"]:
            self.temoin.montrer("Écoute active" if on else "Écoute coupée", "hand" if on else "pause", "Gestes")
        return on

    def enregistrer(self, nouveau: dict) -> None:
        ancien = self.r
        r = reg.nettoyer(reg.fusionner(reg.defauts(), nouveau))
        r["ecoute"] = ancien["ecoute"]           # géré uniquement par basculer()
        self.r = self.service.reglages = r       # remplacement d'un bloc : le fil caméra lit l'un ou l'autre
        reg.appliquer(r)
        reg.enregistrer(r)
        if r["demarrage_windows"] != ancien["demarrage_windows"]:
            demarrage_windows(r["demarrage_windows"])
        if r["camera"] != ancien["camera"] and self.service.en_marche():
            threading.Thread(target=lambda: (self.service.arreter(), self.service.demarrer()), daemon=True).start()

    def ouvrir(self) -> None:
        if self.fenetre:
            self.fenetre.show()
            self.fenetre.restore()

    def quitter(self) -> None:
        self.quitter_demande = True
        self.service.arreter()
        if self.icone:
            self.icone.stop()
        for f in (self.temoin.fenetre, self.fenetre):
            try:
                f and f.destroy()
            except Exception:
                pass

    def _sur_action(self, libelle: str, icone: str, geste: str, ton: str = "") -> None:
        if self.r["temoin"]:
            self.temoin.montrer(libelle, icone, geste, ton)

    # --- démarrage ---
    def au_demarrage(self) -> None:
        threading.Thread(target=self._raccourci_global, daemon=True).start()
        if not pf.MAC:   # sur Mac, l'icône est créée sur le fil principal (voir main)
            threading.Thread(target=self._icone_notification, daemon=True).start()
        self.cameras = lister_cameras(-1)   # avant d'ouvrir la caméra pour de bon
        if self.r["ecoute"]:
            self.service.demarrer()

    def _raccourci_global(self) -> None:
        pf.ecouter_raccourci(lambda: threading.Thread(target=self.basculer, daemon=True).start())

    def _icone_notification(self, detache: bool = False) -> None:
        import pystray
        menu = pystray.Menu(
            pystray.MenuItem("Ouvrir les réglages", lambda *_: self.ouvrir(), default=True),
            pystray.MenuItem("Écoute active", lambda *_: self.basculer(), checked=lambda _: self.r["ecoute"]),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quitter", lambda *_: self.quitter()),
        )
        if detache:   # macOS : l'icône vit dans la boucle de pywebview (NSApplication)
            from AppKit import NSApplication
            self.icone = pystray.Icon("gestes", image_icone(self.r["ecoute"]), "Gestes", menu,
                                      darwin_nsapplication=NSApplication.sharedApplication())
            self.icone.run_detached()
            return
        self.icone = pystray.Icon("gestes", image_icone(self.r["ecoute"]), "Gestes", menu)
        self.icone.run()

    def _maj_icone(self) -> None:
        if self.icone:
            self.icone.icon = image_icone(self.r["ecoute"])
            self.icone.title = "Gestes · " + ("à l'écoute" if self.r["ecoute"] else "en pause")
            self.icone.update_menu()


def image_icone(actif: bool):
    """Tuile sombre, main blanche stylisée, pastille verte quand l'écoute est active."""
    from PIL import Image, ImageDraw
    s = 4   # dessin en 256 px puis réduction : bords lisses
    img = Image.new("RGBA", (64 * s, 64 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2 * s, 2 * s, 62 * s, 62 * s), radius=14 * s, fill=(46, 49, 58, 255))
    blanc = (255, 255, 255, 255)
    for x, haut in ((20, 16), (27, 12), (34, 12), (41, 16)):
        d.rounded_rectangle((x * s, haut * s, (x + 5) * s, 38 * s), radius=3 * s, fill=blanc)
    d.rounded_rectangle((12 * s, 30 * s, 17 * s, 42 * s), radius=3 * s, fill=blanc)    # pouce
    d.rounded_rectangle((17 * s, 30 * s, 46 * s, 52 * s), radius=8 * s, fill=blanc)    # paume
    couleur = (52, 199, 140, 255) if actif else (140, 144, 156, 255)
    d.ellipse((42 * s, 42 * s, 60 * s, 60 * s), fill=couleur, outline=(46, 49, 58, 255), width=3 * s)
    return img.resize((64, 64), Image.LANCZOS)


class Api:
    """Fonctions appelées par l'interface (window.pywebview.api.*)."""

    def __init__(self, appli: Appli) -> None:
        self._a = appli

    def donnees(self) -> dict:
        return {"reglages": self._a.r, "cameras": self._a.cameras, "plateforme": pf.NOM_PLATEFORME,
                "catalogue": {"actions": {k: {"libelle": l, "type": t} for k, (l, t) in ACTIONS.items()},
                              "gestes": GESTES}}

    def etat(self) -> dict:
        e = self._a.service.instantane()
        e["historique"] = [{k: v for k, v in h.items() if not k.startswith("_")} for h in e["historique"]]
        e["ecoute_voulue"] = self._a.r["ecoute"]
        return e

    def enregistrer(self, r: dict) -> bool:
        self._a.enregistrer(r)
        return True

    def basculer(self, on: bool) -> bool:
        return self._a.basculer(on)

    def choisir_application(self):
        mode = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
        types = ("Tous les fichiers (*.*)",) if pf.MAC else ("Applications (*.exe;*.lnk)", "Tous les fichiers (*.*)")
        res = self._a.fenetre.create_file_dialog(mode, file_types=types)
        return res[0] if res else None

    def reduire(self) -> None:
        self._a.fenetre.minimize()

    def fermer(self) -> None:
        self._a.fenetre.hide()


une_seule_instance = pf.une_seule_instance


def verifier() -> int:
    """`--verifier` : charge tout ce que l'app utilise, sans caméra ni fenêtre, puis quitte.
    Sert au workflow de release pour tester l'app empaquetée (0 = tout va bien)."""
    try:
        import cv2  # noqa: F401
        import pyautogui  # noqa: F401
        import pystray  # noqa: F401
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
        from .app import modele
        from .chemins import UI as dossier_ui
        assert (dossier_ui / "index.html").exists(), "interface absente"
        opts = HandLandmarkerOptions(base_options=BaseOptions(model_asset_buffer=modele().read_bytes()),
                                     running_mode=RunningMode.VIDEO, num_hands=1)
        HandLandmarker.create_from_options(opts).close()
        pf.appli_au_premier_plan()
        pf.theme_sombre()
        image_icone(True)
        print("Gestes : vérification OK", flush=True)
        return 0
    except Exception as e:
        print(f"Gestes : vérification en échec : {e!r}", flush=True)
        return 1


def main() -> None:
    if "--verifier" in sys.argv:
        sys.exit(verifier())
    if not une_seule_instance():
        pf.alerte("Gestes tourne déjà : son icône est dans la barre des menus." if pf.MAC
                  else "Gestes tourne déjà : son icône est près de l'horloge.")
        return
    appli = Appli(cache="--cache" in sys.argv, essai="--essai" in sys.argv)
    appli.fenetre = webview.create_window(
        "Gestes", str(UI / "index.html"), js_api=Api(appli), width=1000, height=680, min_size=(860, 560),
        frameless=True, easy_drag=False, hidden=appli.cache,
        background_color="#232428" if theme_sombre() else "#fcfcfd")

    def fermeture():
        if appli.quitter_demande:
            return True
        appli.fenetre.hide()      # la croix range l'app près de l'horloge
        return False
    appli.fenetre.events.closing += fermeture
    appli.temoin.creer()
    if pf.MAC:
        appli._icone_notification(detache=True)
    webview.start(appli.au_demarrage)


if __name__ == "__main__":
    main()
