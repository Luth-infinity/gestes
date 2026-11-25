"""Enregistrement guidé : l'écran dit quel geste faire, chaque image est notée avec ses 21 points.

Sert à régler les seuils sur de vraies mains (et à rejouer les enregistrements dans les tests).
Lancement : enregistrer.bat  (Échap pour arrêter, Espace pour passer une étape)
"""
from __future__ import annotations

import csv
import time
from datetime import datetime

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

from . import config
from .app import ecrire, modele
from .chemins import JOURNAL

# (étiquette, consigne, durée en secondes)
ETAPES = [
    ("rien", "Pas de main devant la camera", 4),
    ("ouverte", "Main ouverte, paume vers la camera, immobile", 5),
    ("poing", "Poing ferme, immobile", 5),
    ("pince", "Pince pouce + index comme TU le fais, immobile", 6),
    ("pince_monte", "Pince et monte / descends lentement, plusieurs fois", 10),
    ("pouce", "Pouce leve", 5),
    ("pointe", "Index leve : vise les 4 coins de l'ecran, sans forcer", 10),
    ("pointe_clic", "Index leve, puis pince pour cliquer. 5 fois, a ton rythme", 12),
    ("balayage_droite", "Main ouverte : balaye vers la DROITE, 4 fois (revient doucement)", 12),
    ("balayage_gauche", "Main ouverte : balaye vers la GAUCHE, 4 fois (revient doucement)", 12),
    ("libre", "Bouge la main naturellement, sans geste precis", 8),
]
PREPARATION = 3.0


def lancer() -> None:
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_buffer=modele().read_bytes()),
        running_mode=RunningMode.VIDEO, num_hands=1,
        min_hand_detection_confidence=config.CONFIANCE_DETECTION,
        min_tracking_confidence=config.CONFIANCE_SUIVI)
    from .camera import ouvrir
    cam = ouvrir(config.CAMERA_INDEX)   # mêmes réglages caméra que l'app
    if cam is None:
        raise SystemExit("Webcam introuvable.")

    dossier = JOURNAL
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"gestes-{datetime.now():%Y%m%d-%H%M%S}.csv"
    with open(chemin, "w", newline="", encoding="utf-8") as f, \
            HandLandmarker.create_from_options(options) as detecteur:
        from .camera import Horodateur
        horloge = Horodateur()
        w = csv.writer(f, delimiter=";")
        w.writerow(["t", "etape", "phase"] + [f"{c}{i}" for i in range(21) for c in "xy"])
        t0 = time.monotonic()
        etape, debut = 0, t0
        while etape < len(ETAPES):
            ok, img = cam.read()
            if not ok:
                break
            if config.MIROIR:
                img = cv2.flip(img, 1)
            maintenant = time.monotonic()
            t = maintenant - t0
            res = detecteur.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)),
                horloge.ms(t))
            pts = [(lm.x, lm.y) for lm in res.hand_landmarks[0]] if res.hand_landmarks else None

            nom, consigne, duree = ETAPES[etape]
            ecoule = maintenant - debut
            phase = "prep" if ecoule < PREPARATION else "rec"
            w.writerow([f"{t:.3f}", nom, phase] +
                       ([f"{v:.4f}" for p in pts for v in p] if pts else [""] * 42))

            # affichage
            h, l = img.shape[:2]
            if pts:
                for x, y in pts:
                    cv2.circle(img, (int(x * l), int(y * h)), 3, (90, 200, 90), -1)
            cv2.rectangle(img, (0, 0), (l, 58), (30, 30, 30), -1)
            ecrire(img, f"{etape + 1}/{len(ETAPES)}  {consigne}", (10, 24), 0.5, (255, 255, 255))
            if phase == "prep":
                ecrire(img, f"Prepare-toi... {PREPARATION - ecoule:.0f}", (10, 48), 0.55, (40, 160, 255), 2)
            else:
                reste = duree - (ecoule - PREPARATION)
                ecrire(img, f"ENREGISTREMENT  {reste:.0f} s", (10, 48), 0.55, (60, 60, 230), 2)
            cv2.imshow("Enregistrement des gestes", img)
            touche = cv2.waitKey(1) & 0xFF
            if touche == 27:
                break
            if touche == 32 or ecoule >= PREPARATION + duree:
                etape, debut = etape + 1, time.monotonic()

    cam.release()
    cv2.destroyAllWindows()
    print(f"Enregistrement : {chemin}")


if __name__ == "__main__":
    lancer()
