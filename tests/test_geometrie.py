"""Mains synthétiques (poignet en bas, doigts vers le haut, y vers le bas)."""
from gestes_webcam.geometrie import Geste, classer

BASES_X = {"index": 0.42, "majeur": 0.50, "annulaire": 0.57, "auriculaire": 0.63}


def doigt(x, tendu):
    base = (x, 0.60)
    if tendu:
        return [base, (x, 0.50), (x, 0.45), (x, 0.40)]
    return [base, (x, 0.50), (x, 0.56), (x, 0.615)]  # bout replié contre sa base (mesuré : 0,08)


def main(tendus=(), pouce="replie", pincement=False):
    pts = [(0.50, 0.80), (0.42, 0.75), (0.36, 0.70), (0.32, 0.65)]
    pts.append({"ecarte": (0.27, 0.60), "replie": (0.48, 0.53), "haut": (0.36, 0.45), "bas": (0.36, 0.78)}[pouce])
    for nom, x in BASES_X.items():
        pts += doigt(x, nom in tendus)
    if pincement:
        pts[8] = (0.36, 0.52)
        pts[4] = (0.35, 0.54)
    return pts


TOUS = ("index", "majeur", "annulaire", "auriculaire")


def test_main_ouverte():
    assert classer(main(TOUS, pouce="ecarte")) is Geste.MAIN_OUVERTE


def test_poing():
    assert classer(main()) is Geste.POING


def test_pouce_leve():
    assert classer(main(pouce="haut")) is Geste.POUCE_LEVE


def test_index_pointe():
    assert classer(main(("index",))) is Geste.POINTER


def test_pincement_en_ok():
    assert classer(main(("majeur", "annulaire", "auriculaire"), pincement=True)) is Geste.PINCEMENT


def test_pincement_tous_doigts_replies():
    # Mesuré : beaucoup de gens pincent en repliant aussi les autres doigts.
    assert classer(main(pincement=True)) is Geste.PINCEMENT


def test_deux_doigts():
    assert classer(main(("index", "majeur"))) is Geste.DEUX_DOIGTS


def test_trois_doigts_non_reconnu():
    assert classer(main(("index", "majeur", "annulaire"))) is Geste.AUCUN


def test_pouce_baisse():
    assert classer(main(pouce="bas")) is Geste.POUCE_BAS


def test_points_incomplets():
    assert classer([(0.5, 0.5)] * 5) is Geste.AUCUN


def test_pincement_naturel_majeur_replie():
    # Pincement spontané : majeur replié, annulaire et auriculaire détendus.
    assert classer(main(("annulaire", "auriculaire"), pincement=True)) is Geste.PINCEMENT


def test_pincement_entrouvert_garde_pendant_le_mouvement():
    p = main(("majeur", "annulaire", "auriculaire"), pincement=True)
    p[4] = (0.35, 0.60)   # pouce un peu décollé de l'index (0,40 × taille de main)
    assert classer(p) is not Geste.PINCEMENT          # pas assez net pour commencer
    assert classer(p, pince_avant=True) is Geste.PINCEMENT   # mais suffit pour continuer
