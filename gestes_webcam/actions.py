"""Exécute sur le PC (Windows ou macOS) l'action choisie pour un évènement du moteur."""
from __future__ import annotations

import os
import time
from collections import deque

from . import config
from .catalogue import ACTIONS
from .moteur import Evenement, vers_ecran
from .plateforme import RACCOURCIS, TOUCHE_FENETRES, TOUCHE_SYSTEME, ouvrir_fichier, touche_media
from .souris import Filtre1Euro, Glisseur

# Noms de touches venant de l'interface -> noms PyAutoGUI
TOUCHES = {"ctrl": "ctrl", "control": "ctrl", "alt": "alt", "maj": "shift", "shift": "shift",
           "win": TOUCHE_SYSTEME, "meta": TOUCHE_SYSTEME, "cmd": "command", "command": "command", "arrowleft": "left", "arrowright": "right", "arrowup": "up",
           "arrowdown": "down", "escape": "esc", "échap": "esc", "enter": "enter", "entrée": "enter",
           " ": "space", "space": "space", "espace": "space", "backspace": "backspace",
           "delete": "delete", "tab": "tab", "pageup": "pageup", "pagedown": "pagedown",
           "home": "home", "end": "end", "printscreen": "printscreen"}

# Raccourcis simples : action -> touches ; pour les directions : (droite, gauche)
SIMPLES = {
    "lecture_pause": ("playpause",), "valider": ("enter",), "annuler": ("esc",), "muet": ("volumemute",),
    "capture": RACCOURCIS["capture"], "vue_taches": RACCOURCIS["vue_taches"],
    "afficher_bureau": RACCOURCIS["afficher_bureau"], "diaporama": ("f5",), "ecran_noir": ("b",),
}
DIRECTIONS = {
    "bureau_virtuel": RACCOURCIS["bureau_virtuel"],
    "fenetre": RACCOURCIS["fenetre"],
    "onglet": (("ctrl", "tab"), ("ctrl", "shift", "tab")),
    "piste": (("nexttrack",), ("prevtrack",)),
    "diapo": (("right",), ("left",)),
}


def vers_pyautogui(touches: list[str]) -> list[str]:
    return [TOUCHES.get(k.lower(), k.lower()) for k in touches]


def libelle(action: str) -> str:
    return ACTIONS.get(action, (action, ""))[0]


class Executeur:
    def __init__(self, essai: bool = False) -> None:
        self.essai = essai
        self.filtre = Filtre1Euro()
        self.glisseur = Glisseur(actif=not essai)
        self.alt_tenu = False
        self._traces: deque[tuple[float, float, float]] = deque(maxlen=60)   # (instant, x, y) du curseur
        import pyautogui
        pyautogui.FAILSAFE = True   # souris dans un coin = arrêt d'urgence
        pyautogui.PAUSE = 0
        self.pg = pyautogui
        self.ecran = pyautogui.size()

    def executer(self, ev: Evenement, choix: dict | None) -> str | None:
        """Exécute l'évènement avec l'action choisie ; renvoie un libellé à afficher."""
        if ev.nom == "arme":
            return "Gestes armés"
        if ev.nom == "desarme":
            return "En veille"
        if ev.nom == "fin" and ev.geste == "choix":
            self._touches("esc")
            return "Choix annulé"
        if ev.nom == "fin":
            self._relacher_alt()
            return None
        if ev.nom == "curseur":
            if ev.pos:
                t = time.monotonic()
                x, y = self.filtre.filtrer(vers_ecran(ev.pos, *self.ecran), t)
                self._traces.append((t, x, y))
                self.glisseur.viser((x, y))
            return None
        if ev.geste == "clic":
            vise = self.position_visee()
            self.glisseur.figer()
            self.filtre.oublier()
            if vise:
                self._faire(self.pg.click, *vise)
            else:
                self._faire(self.pg.click)
            self._traces.clear()
            return "Clic"

        action = (choix or {}).get("action", "rien")
        param = (choix or {}).get("param")
        if action == "rien":
            return None

        if ev.nom == "maintien":
            if action in SIMPLES:
                self._touches(*SIMPLES[action])
            elif action == "raccourci" and param:
                self._touches(*vers_pyautogui(param))
                return " + ".join(param)
            elif action == "lancer" and param:
                self._faire(ouvrir_fichier, param)
                return f"Lancer {os.path.basename(param)}"
            else:
                return None
            return libelle(action)

        if ev.nom in ("debut", "direction"):
            if action == "selecteur":
                if not self.alt_tenu:
                    self._faire(self.pg.keyDown, TOUCHE_FENETRES)
                    self.alt_tenu = True
                self._touches("shift", "tab") if ev.sens < 0 else self._touches("tab")
                return "Sélecteur de fenêtres" if ev.nom == "debut" else None
            if action == "choisir_fenetre":
                self._touches(*RACCOURCIS["choisir_fenetre"])
                return "Pointe une fenêtre, pince pour choisir"
            if action in DIRECTIONS:
                droite, gauche = DIRECTIONS[action]
                self._touches(*(droite if ev.sens > 0 else gauche))
                lib = libelle(action)
                if " / " in lib:
                    return lib.split(" / ")[0] if ev.sens > 0 else _precedent(lib)
                return f"{lib} {'→' if ev.sens > 0 else '←'}"
            return None

        if ev.nom == "continu":
            n = ev.sens
            if action == "volume":
                self._faire(touche_media, self.pg, "volumeup" if n > 0 else "volumedown", abs(n) * 2)
                return "Volume +" if n > 0 else "Volume −"
            if action == "defiler":
                self._faire(self.pg.scroll, n * config.DELTA_DEFILEMENT)
                return None
            if action == "zoom":
                self._touches_avec("ctrl", lambda: self.pg.scroll(n * 120))
                return "Zoom +" if n > 0 else "Zoom −"
        return None

    def position_visee(self) -> tuple[float, float] | None:
        """Où pointait le doigt juste avant le pincement : en pinçant, l'index se courbe
        et la souris glisse un peu. On revient RECUL_CLIC s avant le dernier mouvement."""
        if not self._traces:
            return None
        limite = self._traces[-1][0] - config.RECUL_CLIC
        for t, x, y in reversed(self._traces):
            if t <= limite:
                return x, y
        return self._traces[0][1], self._traces[0][2]

    def relacher_tout(self) -> None:
        self._relacher_alt()
        self.glisseur.arreter()

    # --- interne ---
    def _relacher_alt(self) -> None:
        if self.alt_tenu:
            self._faire(self.pg.keyUp, TOUCHE_FENETRES)
            self.alt_tenu = False

    def _faire(self, fn, *args, **kwargs) -> None:
        if not self.essai:
            fn(*args, **kwargs)

    def _touches(self, *touches: str) -> None:
        if len(touches) == 1:
            if not self.essai and touche_media(self.pg, touches[0]):
                return
            self._faire(self.pg.press, touches[0])
        else:
            self._faire(self.pg.hotkey, *touches)

    def _touches_avec(self, modif: str, fn) -> None:
        if self.essai:
            return
        self.pg.keyDown(modif)
        try:
            fn()
        finally:
            self.pg.keyUp(modif)


def _precedent(lib: str) -> str:
    """« Piste suivante / précédente » -> « Piste précédente »."""
    tete, _, fin = lib.partition(" / ")
    return tete.rsplit(" ", 1)[0] + " " + fin
