"""Contrôle du PC par gestes de la main devant la webcam."""
import os

__version__ = "0.1.0"

# Doit précéder tout import d'OpenCV : ouverture de la webcam en 1,4 s au lieu de 14 (voir camera.py).
os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")
