"""Boucle principale : webcam -> MediaPipe -> geste -> moteur -> action."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import time
import unicodedata
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

from . import config
from .geometrie import INDEX_BASE, Geste, centre_paume, classer, mesures
from .moteur import Moteur

URL_MODELE = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
              "hand_landmarker/float16/1/hand_landmarker.task")
from .chemins import JOURNAL, MODELE
COLONNES = ["t", "geste", "paume_x", "paume_y", "arme", "progression",
            "pincement", "pouce_majeur", "index_deplie", "pouce_ecarte", "pouce_au_dessus", "evenements"]

LIAISONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

VERT, GRIS, BLANC, ORANGE = (90, 200, 90), (150, 150, 150), (255, 255, 255), (40, 160, 255)


def sans_accents(texte: str) -> str:
    """cv2.putText ne sait pas dessiner les accents."""
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()


def ecrire(img, texte, pos, taille, couleur, epaisseur=1) -> None:
    cv2.putText(img, sans_accents(texte), pos, cv2.FONT_HERSHEY_SIMPLEX, taille, couleur, epaisseur)


def modele() -> Path:
    if not MODELE.exists():
        MODELE.parent.mkdir(parents=True, exist_ok=True)
        print("Téléchargement du modèle de main (7 Mo)…")
        urllib.request.urlretrieve(URL_MODELE, MODELE)
    return MODELE


def ouvrir_camera() -> cv2.VideoCapture:
    from .camera import ouvrir
    cam = ouvrir(config.CAMERA_INDEX)
    if cam is None:
        raise SystemExit(f"Webcam {config.CAMERA_INDEX} introuvable. "
                         "Vérifie CAMERA_INDEX dans config.py ou les autorisations caméra de Windows.")
    return cam


def dessiner(img, points, moteur: Moteur, message: str, essai: bool) -> None:
    h, w = img.shape[:2]
    couleur = VERT if moteur.arme else GRIS
    if points:
        px = [(int(x * w), int(y * h)) for x, y in points]
        for a, b in LIAISONS:
            cv2.line(img, px[a], px[b], couleur, 2)
        for p in px:
            cv2.circle(img, p, 3, BLANC, -1)

    cv2.rectangle(img, (0, 0), (w, 70), (30, 30, 30), -1)
    etat = "ARMÉ" if moteur.arme else "EN VEILLE (main ouverte pour armer)"
    ecrire(img, etat, (12, 26), 0.7, couleur, 2)
    ecrire(img, f"Geste : {moteur.geste.value}", (12, 56), 0.6, BLANC)
    if moteur.progression > 0:
        cv2.rectangle(img, (w - 212, 20), (w - 12, 36), GRIS, 1)
        cv2.rectangle(img, (w - 212, 20), (w - 212 + int(200 * moteur.progression), 36), ORANGE, -1)
    if message:
        ecrire(img, message, (12, h - 20), 0.8, ORANGE, 2)
    if essai:
        ecrire(img, "MODE ESSAI : aucune action", (w - 330, h - 20), 0.6, ORANGE)
    if moteur.arme and config.CURSEUR_ACTIF:
        x0, y0, x1, y1 = config.ZONE_CURSEUR
        cv2.rectangle(img, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), GRIS, 1)


def ouvrir_journal(essai: bool):
    dossier = JOURNAL
    dossier.mkdir(parents=True, exist_ok=True)
    nom = f"{'essai' if essai else 'reel'}-{datetime.now():%Y%m%d-%H%M%S}.csv"
    fichier = open(dossier / nom, "w", newline="", encoding="utf-8-sig")
    ecrivain = csv.writer(fichier, delimiter=";")   # point-virgule : Excel en français
    ecrivain.writerow(COLONNES)
    print(f"Journal : {dossier / nom}")
    return fichier, ecrivain


def lancer(essai: bool, journal: bool = False) -> None:
    from .actions import Executeur
    from .profils import appli_au_premier_plan, choix_pour, profil_actif
    from .reglages import actifs, appliquer, charger

    reglages = charger()
    appliquer(reglages)
    actions = Executeur(essai=essai)
    moteur = Moteur(actifs(reglages))
    options = HandLandmarkerOptions(
        # en mémoire : MediaPipe n'ouvre pas les chemins avec accents (« Contrôle »)
        base_options=BaseOptions(model_asset_buffer=modele().read_bytes()),
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=config.CONFIANCE_DETECTION,
        min_tracking_confidence=config.CONFIANCE_SUIVI,
    )
    cam = ouvrir_camera()
    message, fin_message = "", 0.0
    fichier, ecrivain = ouvrir_journal(essai) if journal else (None, None)
    t0 = time.monotonic()
    print("Prêt. Q ou Échap pour quitter, souris dans un coin de l'écran = arrêt d'urgence.")

    from .camera import Horodateur
    horloge = Horodateur()
    with HandLandmarker.create_from_options(options) as detecteur:
        while True:
            ok, img = cam.read()
            if not ok:
                break
            if config.MIROIR:
                img = cv2.flip(img, 1)
            t = time.monotonic() - t0
            rgb = mp.Image(image_format=mp.ImageFormat.SRGB,
                           data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            res = detecteur.detect_for_video(rgb, horloge.ms(t))

            points = None
            if res.hand_landmarks:
                points = [(lm.x, lm.y) for lm in res.hand_landmarks[0]]
            geste = classer(points, moteur.geste is Geste.PINCEMENT, moteur.clic_attendu(t)) if points else Geste.AUCUN
            paume = centre_paume(points) if points else None
            curseur = points[INDEX_BASE] if points else None

            evenements = moteur.mettre_a_jour(geste, paume, t, curseur)
            if ecrivain:
                m = mesures(points) if points else {}
                ecrivain.writerow([
                    f"{t:.3f}", geste.value,
                    *((f"{paume[0]:.3f}", f"{paume[1]:.3f}") if paume else ("", "")),
                    int(moteur.arme), f"{moteur.progression:.2f}",
                    *(f"{m[k]:.3f}" if k in m else "" for k in COLONNES[6:11]),
                    " ".join(e.nom for e in evenements if e.nom != "curseur"),
                ])
            for ev in evenements:
                cle = "pointer" if ev.geste == "clic" else ev.geste
                profil = profil_actif(reglages["profils"], *appli_au_premier_plan())
                choix = choix_pour(reglages, profil, cle) if cle else None
                libelle = actions.executer(ev, choix)
                if ev.nom == "direction" and (choix or {}).get("action") == "choisir_fenetre":
                    moteur.entrer_mode_choix(t)
                if libelle:
                    print(f"[{t:7.2f}s] {libelle}")
                    message, fin_message = libelle, t + 1.5

            dessiner(img, points, moteur, message if t < fin_message else "", essai)
            cv2.imshow("Gestes webcam", img)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

    actions.relacher_tout()
    cam.release()
    cv2.destroyAllWindows()
    if fichier:
        fichier.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Contrôle du PC par gestes de la main.")
    parser.add_argument("--essai", action="store_true",
                        help="reconnaît les gestes et affiche les actions sans les exécuter")
    parser.add_argument("--journal", action="store_true",
                        help="enregistre le geste et les mesures de chaque image dans journal/")
    args = parser.parse_args()
    lancer(args.essai, args.journal)


if __name__ == "__main__":
    main()
