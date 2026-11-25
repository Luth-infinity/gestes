"""Vérifie, dans l'app empaquetée, chaque étape du démarrage de la caméra."""
import time, traceback
t0 = time.time()
def etape(m): print(f"[{time.time()-t0:5.1f}s] {m}", flush=True)
try:
    import gestes_webcam  # noqa: F401  (variable MSMF)
    etape("import gestes_webcam")
    from gestes_webcam.chemins import MODELE, UI, JOURNAL
    etape(f"modele {MODELE} existe={MODELE.exists()} ui={UI.exists()} journal={JOURNAL}")
    import cv2; etape(f"cv2 {cv2.__version__}")
    import mediapipe as mp; etape(f"mediapipe {mp.__version__}")
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
    opts = HandLandmarkerOptions(base_options=BaseOptions(model_asset_buffer=MODELE.read_bytes()),
                                 running_mode=RunningMode.VIDEO, num_hands=1)
    det = HandLandmarker.create_from_options(opts); etape("HandLandmarker créé")
    from gestes_webcam.camera import ouvrir
    cam = ouvrir(0); etape(f"caméra ouverte={cam is not None}")
    ok, img = cam.read(); etape(f"image {ok} {getattr(img,'shape',None)}")
    res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), 1)
    etape(f"détection OK, mains={len(res.hand_landmarks)}")
    cam.release()
except Exception:
    traceback.print_exc()
input("Entrée pour fermer") if False else None
