"""Transforme une suite de gestes image par image en évènements fiables.

Trois familles de gestes :
- tenus (poing, pouce levé, pouce baissé) : déclenchent une fois après un court maintien ;
- directionnels (balayage, attraper-glisser-lâcher) : donnent un sens, gauche ou droite ;
- continus (pincer et monter, deux doigts) : donnent des crans vers le haut ou le bas.

Le système est désarmé au départ : seule la main ouverte tenue l'arme.
Sans geste pendant DUREE_ARMEMENT, il se désarme tout seul.
Le moteur ne fait que décider ; l'action réelle est choisie ailleurs (actions.py).
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

from . import config
from .geometrie import Geste, Point

TOUS_LES_GESTES = ("attraper", "balayage", "poing", "pincer", "pouce", "pouce_bas", "deux_doigts", "pointer")

MAINTIEN = {Geste.POING: "poing", Geste.POUCE_LEVE: "pouce", Geste.POUCE_BAS: "pouce_bas"}
IMMOBILES_NON_REQUIS = (Geste.POINTER, Geste.PINCEMENT, Geste.DEUX_DOIGTS)
DELAI_POINTER_CLIC = 1.5   # un pincement juste après avoir pointé = clic


@dataclass
class Evenement:
    nom: str                 # arme, desarme, maintien, direction, debut, fin, continu, curseur
    geste: str | None = None
    sens: int = 0            # direction : +1 droite / -1 gauche ; continu : crans, + = vers le haut
    pos: Point | None = None


class Moteur:
    def __init__(self, actifs=None) -> None:
        self.actifs: set[str] = set(TOUS_LES_GESTES if actifs is None else actifs)
        self.arme = False
        self.fin_armement = 0.0
        self.geste = Geste.AUCUN
        self.progression = 0.0
        self.attrape = False
        self._debut = 0.0
        self._pos_debut: Point | None = None
        self._origine: Point | None = None      # position au début du geste (ne bouge pas)
        self._declenche = False
        self._trace: deque[tuple[float, float, float, Geste]] = deque()
        self._dernier_balayage = -math.inf
        self._sens_balayage = 0
        self._dernier_clic = -math.inf
        self._dernier_pointer = -math.inf
        self._pince_clic = False
        self._y_ref = 0.0
        self._x_ref = 0.0
        self._hors_poing: float | None = None
        self._debut_attrape = 0.0
        self._vu = 0.0
        self._vu_pince = -math.inf
        self._fin_choix = 0.0       # mode « choisir une fenêtre » actif jusqu'à cet instant

    # ------------------------------------------------------------------ API
    @property
    def en_choix(self) -> bool:
        return self._fin_choix > 0

    def clic_attendu(self, t: float) -> bool:
        """Vrai si un pincement maintenant serait un clic (on vient de pointer)."""
        if "pointer" not in self.actifs or not (self.arme or self.en_choix):
            return False
        return self.en_choix or t - self._dernier_pointer < DELAI_POINTER_CLIC

    def entrer_mode_choix(self, t: float) -> None:
        """Vue des fenêtres ouverte : le doigt guide la souris, un pincement choisit, le poing annule."""
        self._fin_choix = t + config.DUREE_MODE_CHOIX
        self._changer(Geste.AUCUN, t, None)
        self._prolonger(t)

    def mettre_a_jour(self, geste: Geste, paume: Point | None, t: float,
                      curseur: Point | None = None) -> list[Evenement]:
        ev: list[Evenement] = []
        if self.arme and not self.attrape and t > self.fin_armement:
            self.arme = False
            ev.append(Evenement("desarme"))

        if self.en_choix and t > self._fin_choix:
            self._fin_choix = 0.0
            ev.append(Evenement("fin", "choix"))
        if paume is None:
            if self.attrape and t - self._vu > config.PERTE_MAX:
                self._finir_attrape(ev)
            if not self.attrape:
                self._changer(Geste.AUCUN, t, None)
            return ev
        self._vu = t

        # Pincement perdu un court instant (main qui bouge) : on le garde, le volume continue.
        if geste is Geste.PINCEMENT:
            self._vu_pince = t
        elif (geste is Geste.AUCUN and self.geste is Geste.PINCEMENT
              and t - self._vu_pince < config.TOLERANCE_PINCEMENT):
            geste = Geste.PINCEMENT

        if self.attrape:
            self._suivre_attrape(geste, paume, t, ev)
            return ev

        if self.en_choix:
            self._choix(geste, paume, t, curseur, ev)
            return ev

        if not self.arme:
            self._suivre_geste(geste, paume, t)
            self._maintien(geste, t, ev, "arme" if geste is Geste.MAIN_OUVERTE else None,
                           config.DUREE_ACTIVATION)
            return ev

        sens = self._balayage(geste, paume, t)
        if sens:
            ev.append(Evenement("direction", "balayage", sens))
            self._prolonger(t)
            self._suivre_geste(geste, paume, t)
            self._declenche = True
            return ev

        self._suivre_geste(geste, paume, t)

        # Poing qui se déplace : début d'« attraper ».
        if (geste is Geste.POING and "attraper" in self.actifs and not self._declenche
                and abs(paume[0] - self._origine[0]) > config.SEUIL_ATTRAPER):
            sens = 1 if paume[0] > self._origine[0] else -1
            self.attrape, self._debut_attrape, self._x_ref = True, t, paume[0]
            self._hors_poing, self.progression = None, 0.0
            self._trace.clear()
            self._prolonger(t)
            ev.append(Evenement("debut", "attraper", sens))
            return ev

        continu = self._continu(geste)
        if continu and t - self._debut < config.DEBUT_CONTINU:
            self._y_ref = paume[1]          # pas encore sûr : le volume part d'ici
            self.progression = 0.0
            return ev
        if continu:
            pas = config.PAS_DEFILEMENT if continu == "deux_doigts" else config.PAS_CONTINU
            crans = int((self._y_ref - paume[1]) / pas)
            if crans:
                self._y_ref -= crans * pas
                self._prolonger(t)
                ev.append(Evenement("continu", continu, crans))
            self.progression = 0.0
            return ev

        if geste is Geste.POINTER and "pointer" in self.actifs:
            self._dernier_pointer = t
            self.progression = 0.0
            if curseur is not None:
                ev.append(Evenement("curseur", "pointer", pos=curseur))
            self._prolonger(t)
            return ev

        if geste is Geste.PINCEMENT and self._pince_clic:
            self._maintien(geste, t, ev, "clic", config.DUREE_PINCEMENT)
        elif geste in MAINTIEN and MAINTIEN[geste] in self.actifs:
            self._maintien(geste, t, ev, MAINTIEN[geste], config.DUREE_MAINTIEN)
        else:
            self.progression = 0.0
        return ev

    # -------------------------------------------------------------- interne
    def _changer(self, geste: Geste, t: float, paume: Point | None) -> None:
        self.geste = geste
        self._debut = t
        self._pos_debut = self._origine = paume
        self._declenche = False
        self.progression = 0.0
        if paume is not None:
            self._y_ref = paume[1]
        self._pince_clic = geste is Geste.PINCEMENT and "pointer" in self.actifs and (
            t - self._dernier_pointer < DELAI_POINTER_CLIC or "pincer" not in self.actifs)

    def _suivre_geste(self, geste: Geste, paume: Point, t: float) -> None:
        if geste is not self.geste:
            self._changer(geste, t, paume)
        elif (geste not in IMMOBILES_NON_REQUIS and self._pos_debut is not None
              and math.dist(paume, self._pos_debut) > config.SEUIL_IMMOBILE):
            self._debut, self._pos_debut, self.progression = t, paume, 0.0   # la main bouge

    def _prolonger(self, t: float) -> None:
        self.fin_armement = t + config.DUREE_ARMEMENT

    def _maintien(self, geste: Geste, t: float, ev: list[Evenement], nom: str | None, duree: float) -> None:
        if nom is None or self._declenche:
            self.progression = 0.0 if nom is None else self.progression
            return
        self.progression = min((t - self._debut) / duree, 1.0)
        if self.progression < 1.0:
            return
        self._declenche = True
        if nom == "clic":
            if t - self._dernier_clic < config.DELAI_ENTRE_CLICS:
                return
            self._dernier_clic = t
            ev.append(Evenement("maintien", "clic"))
        elif nom == "arme":
            self.arme = True
            ev.append(Evenement("arme"))
        else:
            ev.append(Evenement("maintien", nom))
        self._prolonger(t)

    def _continu(self, geste: Geste) -> str | None:
        if geste is Geste.PINCEMENT and not self._pince_clic and "pincer" in self.actifs:
            return "pincer"
        if geste is Geste.DEUX_DOIGTS and "deux_doigts" in self.actifs:
            return "deux_doigts"
        return None

    def _suivre_attrape(self, geste: Geste, paume: Point, t: float, ev: list[Evenement]) -> None:
        self._prolonger(t)
        if t - self._debut_attrape > config.ATTRAPER_MAX:
            self._finir_attrape(ev)
            return
        if geste in (Geste.POING, Geste.AUCUN):
            self._hors_poing = None
            while abs(paume[0] - self._x_ref) >= config.PAS_ATTRAPER:
                sens = 1 if paume[0] > self._x_ref else -1
                self._x_ref += sens * config.PAS_ATTRAPER
                ev.append(Evenement("direction", "attraper", sens))
            return
        if self._hors_poing is None:
            self._hors_poing = t
        elif t - self._hors_poing > config.LACHER:
            self._finir_attrape(ev)
            self._changer(geste, t, paume)
            self._declenche = True

    def _choix(self, geste: Geste, paume: Point, t: float, curseur: Point | None,
               ev: list[Evenement]) -> None:
        self._suivre_geste(geste, paume, t)
        self._prolonger(t)
        if geste is Geste.POINTER:
            self._dernier_pointer = t
            self._fin_choix = max(self._fin_choix, t + config.DUREE_MODE_CHOIX / 2)
            self.progression = 0.0
            if curseur is not None:
                ev.append(Evenement("curseur", "pointer", pos=curseur))
        elif geste is Geste.PINCEMENT:
            n = len(ev)
            self._maintien(geste, t, ev, "clic", config.DUREE_PINCEMENT)
            if len(ev) > n:
                self._fin_choix = 0.0           # la fenêtre est choisie, la vue se ferme seule
        elif geste is Geste.POING:
            n = len(ev)
            self._maintien(geste, t, ev, "annuler_choix", config.DUREE_MAINTIEN)
            if len(ev) > n:
                ev[-1] = Evenement("fin", "choix")
                self._fin_choix = 0.0
        else:
            self.progression = 0.0

    def _finir_attrape(self, ev: list[Evenement]) -> None:
        self.attrape = False
        self._trace.clear()
        ev.append(Evenement("fin", "attraper"))

    def _balayage(self, geste: Geste, paume: Point, t: float) -> int:
        if "balayage" not in self.actifs:
            return 0
        # La main peut changer de forme pendant le geste ; seuls les gestes qui
        # bougent volontairement (curseur, défilement, volume, attraper) l'empêchent.
        self._trace.append((t, paume[0], paume[1], geste))
        while self._trace and t - self._trace[0][0] > config.FENETRE_BALAYAGE:
            self._trace.popleft()
        if t - self._dernier_balayage < config.DELAI_ENTRE_BALAYAGES:
            return 0
        bloquants = {Geste.POINTER, Geste.DEUX_DOIGTS, Geste.PINCEMENT}
        if "attraper" in self.actifs:
            bloquants.add(Geste.POING)
        # Une image floue mal classée ne suffit pas à bloquer : il en faut plusieurs.
        if sum(g in bloquants for *_, g in self._trace) >= config.BLOQUANTS_MIN:
            return 0
        _, x0, y0, _ = self._trace[0]
        dx, dy = paume[0] - x0, paume[1] - y0
        if abs(dx) > config.DISTANCE_BALAYAGE and abs(dy) < abs(dx) * 0.7:
            sens = 1 if dx > 0 else -1
            self._trace.clear()
            # Retour de la main juste après un balayage : ce n'est pas un balayage inverse.
            if sens == -self._sens_balayage and t - self._dernier_balayage < config.ANTI_RETOUR:
                return 0
            self._dernier_balayage, self._sens_balayage = t, sens
            return sens
        return 0


def vers_ecran(p: Point, largeur: int, hauteur: int, zone=None) -> Point:
    """Projette un point de la zone utile de l'image sur tout l'écran."""
    x0, y0, x1, y1 = zone or config.ZONE_CURSEUR
    fx = min(max((p[0] - x0) / (x1 - x0), 0.0), 1.0)
    fy = min(max((p[1] - y0) / (y1 - y0), 0.0), 1.0)
    return fx * (largeur - 1), fy * (hauteur - 1)
