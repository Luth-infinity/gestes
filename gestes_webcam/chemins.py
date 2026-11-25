"""Où trouver les fichiers, en développement comme dans l'app empaquetée (PyInstaller).

Empaquetée, l'app est installée dans un dossier en lecture seule (Program Files) :
les ressources (modèle, interface) sont livrées avec elle, le journal va dans %LOCALAPPDATA% (Windows) ou ~/Library/Application Support (macOS).
"""
from __future__ import annotations

import sys
from pathlib import Path

from .plateforme import dossier_donnees

FIGEE = bool(getattr(sys, "frozen", False))
RACINE = Path(__file__).resolve().parent.parent
RESSOURCES = Path(getattr(sys, "_MEIPASS", RACINE)) if FIGEE else RACINE
DONNEES = dossier_donnees() if FIGEE else RACINE

UI = RESSOURCES / "gestes_webcam" / "ui"
JOURNAL = DONNEES / "journal"
MODELE_LIVRE = RESSOURCES / "modeles" / "hand_landmarker.task"
MODELE = MODELE_LIVRE if MODELE_LIVRE.exists() else DONNEES / "modeles" / "hand_landmarker.task"


def commande_demarrage() -> list[str]:
    """Commande du lancement à l'ouverture de session (en arrière-plan)."""
    if FIGEE:
        return [sys.executable, "--cache"]
    python = Path(sys.executable)
    if python.with_name("pythonw.exe").exists():
        python = python.with_name("pythonw.exe")
    return [str(python), str(RACINE / "gestes.pyw"), "--cache"]
