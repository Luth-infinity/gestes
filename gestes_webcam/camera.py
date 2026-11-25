"""Ouverture de la webcam, la même pour l'app, le diagnostic et l'enregistrement.

Mesuré sur la webcam de l'utilisateur : DirectShow plafonne à 15 images/s ; Media Foundation
(MSMF) en MJPG en donne 30. MSMF met 14 s à s'ouvrir avec les transformations matérielles,
1,4 s sans : on les coupe (avant le premier usage d'OpenCV).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")

import cv2  # noqa: E402

LARGEUR, HAUTEUR, IPS = 640, 360, 30


def ouvrir(index: int):
    """Renvoie une caméra ouverte qui donne des images, ou None. MSMF d'abord, DirectShow en secours."""
    from .plateforme import backends_camera
    for backend in backends_camera():
        cam = cv2.VideoCapture(index, backend)
        cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, LARGEUR)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HAUTEUR)
        cam.set(cv2.CAP_PROP_FPS, IPS)
        if cam.isOpened() and cam.read()[0]:
            return cam
        cam.release()
    return None


class Horodateur:
    """Millisecondes strictement croissantes pour MediaPipe (detect_for_video).

    MSMF livre parfois deux images à moins d'une milliseconde d'écart : même horodatage,
    et MediaPipe s'arrête (« Input timestamp must be monotonically increasing »).
    """

    def __init__(self) -> None:
        self.dernier = -1

    def ms(self, t: float) -> int:
        self.dernier = max(int(t * 1000), self.dernier + 1)
        return self.dernier
