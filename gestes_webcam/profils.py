"""Profils : l'action d'un geste peut changer selon l'application au premier plan."""
from __future__ import annotations

from .plateforme import appli_au_premier_plan  # noqa: F401  (utilisée par service.py)


def profil_actif(profils: list[dict], exe: str, titre: str) -> dict:
    defaut = next((p for p in profils if p.get("defaut")), profils[0])
    titre_min = titre.lower()
    for p in profils:
        if p.get("defaut") or not p.get("actif", True):
            continue
        if exe and exe in [a.lower() for a in p.get("apps", [])]:
            return p
        if any(m.lower() in titre_min for m in p.get("titres", []) if m):
            return p
    return defaut


def choix_pour(reglages: dict, profil: dict, geste: str) -> dict:
    """Action retenue pour un geste : celle du profil si elle existe, sinon celle de base."""
    base = reglages["gestes"].get(geste, {"action": "rien"})
    return profil.get("actions", {}).get(geste) or base
