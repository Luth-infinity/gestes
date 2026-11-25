"""Réglages de l'utilisateur, enregistrés dans %APPDATA%\\Gestes\\reglages.json
(~/Library/Application Support/Gestes sur macOS)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from . import config
from .catalogue import ACTIONS, GESTES, GESTES_PAR_ID, PROFILS
from .plateforme import dossier_reglages

DOSSIER = dossier_reglages()
FICHIER = DOSSIER / "reglages.json"


def defauts() -> dict:
    return {
        "ecoute": True,
        "camera": 0,
        "temoin": True,
        "demarrage_windows": False,
        "gestes": {g["id"]: {"actif": g["actif"], "action": g["action"], "param": None} for g in GESTES},
        "profils": copy.deepcopy(PROFILS),
        "confort": {"maintien": 0.6, "veille": 6, "balayage": 0.15, "lissage": 0.65, "gaucher": False},
    }


def fusionner(base: dict, ajout: dict) -> dict:
    """Recopie `ajout` dans `base` en gardant les clés par défaut absentes du fichier."""
    for cle, val in ajout.items():
        if isinstance(val, dict) and isinstance(base.get(cle), dict):
            fusionner(base[cle], val)
        else:
            base[cle] = val
    return base


def nettoyer(r: dict) -> dict:
    """Écarte ce qui ne correspond plus au catalogue (ancien fichier, saisie bizarre)."""
    for gid in list(r["gestes"]):
        g = GESTES_PAR_ID.get(gid)
        if g is None:
            del r["gestes"][gid]
            continue
        a = r["gestes"][gid].get("action")
        if a not in ACTIONS or ACTIONS[a][1] not in (g["type"], "*"):
            r["gestes"][gid]["action"] = g["action"]
    return r


def charger(fichier: Path = FICHIER) -> dict:
    r = defauts()
    try:
        fusionner(r, json.loads(fichier.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return nettoyer(r)


def enregistrer(r: dict, fichier: Path = FICHIER) -> None:
    fichier.parent.mkdir(parents=True, exist_ok=True)
    tmp = fichier.with_suffix(".tmp")
    tmp.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(fichier)


def appliquer(r: dict) -> None:
    """Reporte les réglages de confort dans config, lu par le moteur à chaque image."""
    c = r["confort"]
    config.DUREE_MAINTIEN = float(c["maintien"])
    config.DUREE_ARMEMENT = float(c["veille"])
    config.DISTANCE_BALAYAGE = float(c["balayage"])
    config.COUPURE_MIN = 0.3 + 3.0 * (1.0 - float(c["lissage"]))   # lissage 0,65 -> 1,35 Hz
    config.CAMERA_INDEX = int(r["camera"])


def actifs(r: dict) -> set[str]:
    return {gid for gid, g in r["gestes"].items() if g["actif"]}
