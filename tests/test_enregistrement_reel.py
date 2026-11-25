"""Rejoue un vrai enregistrement (enregistrer.bat) : les seuils doivent tenir sur une vraie main."""
import csv
from collections import Counter
from pathlib import Path

import pytest

from gestes_webcam.geometrie import Geste, classer

FICHIER = Path(__file__).parent / "donnees" / "enregistrement-reel.csv"


def _etapes():
    par = {}
    with open(FICHIER, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["phase"] == "rec" and r["x0"]:
                pts = [(float(r[f"x{i}"]), float(r[f"y{i}"])) for i in range(21)]
                par.setdefault(r["etape"], []).append(pts)
    return par


ETAPES = _etapes()


def part(etape, geste, hysteresis=False):
    vus, prec = Counter(), Geste.AUCUN
    for p in ETAPES[etape]:
        prec = classer(p, hysteresis and prec is Geste.PINCEMENT)
        vus[prec] += 1
    return vus[geste] / sum(vus.values())


@pytest.mark.parametrize("etape, geste, mini", [
    ("ouverte", Geste.MAIN_OUVERTE, 0.98),
    ("poing", Geste.POING, 0.85),          # le reste : transitions en début d'étape
    ("pouce", Geste.POUCE_LEVE, 0.95),
    ("pince_monte", Geste.PINCEMENT, 0.98),
])
def test_geste_reconnu(etape, geste, mini):
    assert part(etape, geste) >= mini


def test_pincement_immobile_tenu_grace_a_l_hysteresis():
    # Les images manquées sont la première seconde, le temps que la main se mette en place.
    assert part("pince", Geste.PINCEMENT, hysteresis=True) >= 0.85


def test_le_poing_n_est_jamais_un_pincement():
    assert part("poing", Geste.PINCEMENT) == 0


def test_balayage_presque_jamais_pris_pour_un_pincement():
    for etape in ("balayage_droite", "balayage_gauche"):
        assert part(etape, Geste.PINCEMENT) <= 0.02


def test_seuils_de_clic_ne_prennent_pas_le_poing_pour_un_clic():
    # Juste après avoir pointé, le pincement est reconnu plus largement :
    # le vrai poing ne doit toujours jamais passer pour un clic.
    for p in ETAPES["poing"]:
        assert classer(p, clic=True) is not Geste.PINCEMENT


def test_seuils_de_clic_reconnaissent_au_moins_autant_le_pincement():
    normal = sum(classer(p) is Geste.PINCEMENT for p in ETAPES["pince"])
    clic = sum(classer(p, clic=True) is Geste.PINCEMENT for p in ETAPES["pince"])
    assert clic >= normal
