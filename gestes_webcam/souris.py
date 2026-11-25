"""Curseur fluide : filtre « 1 € » sur la position du doigt, puis glissement à 120 Hz.

La caméra donne une position 30 fois par seconde au mieux : déplacer la souris à ce
rythme fait des sauts. Ici, chaque image ne fait que fixer une cible ; un fil à part
fait glisser le curseur vers elle en douceur.

Le filtre 1 € (Casiez et al., 2012) lisse fort quand le doigt est presque immobile
(fini le tremblement) et presque plus quand il bouge vite (pas de retard).
"""
from __future__ import annotations

import math
import threading
import time

from . import config

Point = tuple[float, float]


class _Filtre1D:
    def __init__(self) -> None:
        self.x: float | None = None
        self.dx = 0.0

    @staticmethod
    def _alpha(coupure: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * coupure)
        return 1.0 / (1.0 + tau / dt)

    def filtrer(self, x: float, dt: float, coupure_min: float, beta: float) -> float:
        if self.x is None or dt <= 0:
            self.x = x
            return x
        a_d = self._alpha(1.0, dt)
        self.dx = self.dx + a_d * ((x - self.x) / dt - self.dx)
        coupure = coupure_min + beta * abs(self.dx)
        self.x = self.x + self._alpha(coupure, dt) * (x - self.x)
        return self.x


class Filtre1Euro:
    """Filtre 1 € en 2D, en pixels d'écran. `t` en secondes."""

    def __init__(self, coupure_min: float | None = None, beta: float | None = None) -> None:
        self.coupure_min = coupure_min
        self.beta = beta
        self._fx, self._fy = _Filtre1D(), _Filtre1D()
        self._t: float | None = None

    def filtrer(self, p: Point, t: float) -> Point:
        cmin = config.COUPURE_MIN if self.coupure_min is None else self.coupure_min
        beta = config.BETA_CURSEUR if self.beta is None else self.beta
        dt = 0.0 if self._t is None else t - self._t
        self._t = t
        return self._fx.filtrer(p[0], dt, cmin, beta), self._fy.filtrer(p[1], dt, cmin, beta)

    def oublier(self) -> None:
        self.__init__(self.coupure_min, self.beta)


class Glisseur:
    """Fait glisser le vrai curseur vers la cible à 120 Hz, dans un fil à part."""

    PERIODE = 1 / 120
    LIBRE_APRES = 0.25       # sans nouvelle cible depuis ce délai, on rend la souris

    def __init__(self, actif: bool = True) -> None:
        self.actif = actif
        self._cible: Point | None = None
        self._pos: Point | None = None
        self._maj = 0.0
        self._verrou = threading.Lock()
        self._stop = threading.Event()
        self._fil: threading.Thread | None = None

    def viser(self, p: Point) -> None:
        with self._verrou:
            if self._cible is None or time.monotonic() - self._maj > self.LIBRE_APRES:
                self._pos = None      # reprise : on part de là où est la souris
            self._cible, self._maj = p, time.monotonic()
        if self.actif and not (self._fil and self._fil.is_alive()):
            self._stop.clear()
            self._fil = threading.Thread(target=self._boucle, name="gestes-souris", daemon=True)
            self._fil.start()

    def figer(self) -> None:
        """Arrête le glissement (avant un clic : le curseur ne doit plus bouger)."""
        with self._verrou:
            self._cible = None

    def arreter(self) -> None:
        self._stop.set()

    def _boucle(self) -> None:
        from .plateforme import placer_curseur, position_curseur
        while not self._stop.is_set():
            with self._verrou:
                cible = self._cible
                if cible and time.monotonic() - self._maj > self.LIBRE_APRES:
                    cible = self._cible = None
                if cible:
                    if self._pos is None:
                        self._pos = position_curseur() or cible
                    k = config.SUIVI_GLISSEMENT
                    x, y = self._pos
                    self._pos = (x + (cible[0] - x) * k, y + (cible[1] - y) * k)
                    pos = self._pos
            if cible:
                placer_curseur(int(round(pos[0])), int(round(pos[1])))
            time.sleep(self.PERIODE)
