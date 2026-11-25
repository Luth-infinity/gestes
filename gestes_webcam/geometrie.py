"""Reconnaissance d'un geste statique à partir des 21 points MediaPipe.

Les règles s'appuient sur des distances relatives à la taille de la main :
elles tiennent quand la main s'éloigne ou s'approche de la caméra.
"""
from __future__ import annotations

import math
from enum import Enum
from typing import Sequence

from . import config

Point = tuple[float, float]

POIGNET = 0
POUCE_IP, POUCE_BOUT = 3, 4
INDEX_BASE, INDEX_PIP, INDEX_BOUT = 5, 6, 8
MAJEUR_BASE, MAJEUR_PIP, MAJEUR_BOUT = 9, 10, 12
ANNULAIRE_PIP, ANNULAIRE_BOUT = 14, 16
AURICULAIRE_PIP, AURICULAIRE_BOUT = 18, 20


class Geste(str, Enum):
    AUCUN = "aucun"
    MAIN_OUVERTE = "main ouverte"
    POING = "poing"
    POUCE_LEVE = "pouce levé"
    POUCE_BAS = "pouce baissé"
    DEUX_DOIGTS = "deux doigts"
    POINTER = "index pointé"
    PINCEMENT = "pincement"


def _d(a: Point, b: Point) -> float:
    return math.dist(a, b)


def taille_main(p: Sequence[Point]) -> float:
    return max(_d(p[POIGNET], p[MAJEUR_BASE]), 1e-6)


def centre_paume(p: Sequence[Point]) -> Point:
    ids = (POIGNET, INDEX_BASE, MAJEUR_BASE, 13, 17)
    return (sum(p[i][0] for i in ids) / 5, sum(p[i][1] for i in ids) / 5)


def _tendu(p: Sequence[Point], bout: int, pip: int) -> bool:
    return _d(p[POIGNET], p[bout]) > _d(p[POIGNET], p[pip]) * config.RATIO_DOIGT_TENDU


def mesures(p: Sequence[Point]) -> dict[str, float]:
    """Les ratios utilisés par classer(), pour régler les seuils à partir du journal."""
    t = taille_main(p)
    return {
        "pincement": _d(p[POUCE_BOUT], p[INDEX_BOUT]) / t,
        "pouce_majeur": _d(p[POUCE_BOUT], p[MAJEUR_PIP]) / t,
        "index_deplie": _d(p[INDEX_BOUT], p[INDEX_BASE]) / t,
        "pouce_ecarte": _d(p[POUCE_BOUT], p[INDEX_BASE]) / t,
        "pouce_au_dessus": (p[INDEX_BASE][1] - p[POUCE_BOUT][1]) / t,
    }


def classer(p: Sequence[Point], pince_avant: bool = False, clic: bool = False) -> Geste:
    """Renvoie le geste reconnu pour une main (points normalisés, y vers le bas).

    `pince_avant` : la main pinçait à l'image précédente, le seuil est alors plus tolérant.
    `clic` : la main vient de pointer, un pincement est attendu (seuils de clic, plus larges).
    """
    if len(p) != 21:
        return Geste.AUCUN
    t = taille_main(p)

    index = _tendu(p, INDEX_BOUT, INDEX_PIP)
    majeur = _tendu(p, MAJEUR_BOUT, MAJEUR_PIP)
    annulaire = _tendu(p, ANNULAIRE_BOUT, ANNULAIRE_PIP)
    auriculaire = _tendu(p, AURICULAIRE_BOUT, AURICULAIRE_PIP)
    pouce = _d(p[POUCE_BOUT], p[INDEX_BASE]) / t > config.POUCE_ECARTE
    autres_plies = not (majeur or annulaire or auriculaire)

    # Pincement d'abord : il ressemble à plusieurs autres gestes.
    # Mesuré sur de vraies mains : dans un poing, le pouce se pose sur le majeur et le bout
    # de l'index rentre contre sa base ; dans un pincement, le pouce va chercher le bout de
    # l'index, loin du majeur. Les autres doigts peuvent être tendus ou repliés.
    seuil = config.SEUIL_PINCEMENT_TENU if pince_avant else config.SEUIL_PINCEMENT
    loin_du_majeur = config.POUCE_LOIN_DU_MAJEUR
    if clic:
        seuil = max(seuil, config.SEUIL_PINCEMENT_CLIC)
        loin_du_majeur = config.POUCE_LOIN_DU_MAJEUR_CLIC
    if (_d(p[POUCE_BOUT], p[INDEX_BOUT]) / t < seuil
            and _d(p[POUCE_BOUT], p[MAJEUR_PIP]) / t > loin_du_majeur
            and _d(p[INDEX_BOUT], p[INDEX_BASE]) / t > config.INDEX_DEPLIE_PINCEMENT):
        return Geste.PINCEMENT

    if index and majeur and annulaire and auriculaire:
        return Geste.MAIN_OUVERTE

    if index and autres_plies:
        return Geste.POINTER

    if index and majeur and not annulaire and not auriculaire:
        return Geste.DEUX_DOIGTS

    if not index and autres_plies:
        pouce_haut = (p[INDEX_BASE][1] - p[POUCE_BOUT][1]) / t > config.POUCE_AU_DESSUS
        pouce_bas = (p[POUCE_BOUT][1] - p[INDEX_BASE][1]) / t > config.POUCE_AU_DESSUS
        if pouce and pouce_haut:
            return Geste.POUCE_LEVE
        if pouce and pouce_bas:
            return Geste.POUCE_BAS
        if not pouce:
            return Geste.POING

    return Geste.AUCUN
