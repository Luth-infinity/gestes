"""Fait tourner caméra + reconnaissance + actions dans un fil d'exécution à part."""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime

from . import config
from .catalogue import GESTES_PAR_ID
from .geometrie import INDEX_BASE, Geste, centre_paume, classer, mesures
from .moteur import Moteur
from .profils import appli_au_premier_plan, choix_pour, profil_actif
from .reglages import actifs

ICONES = {"arme": "hand", "desarme": "moon", "clic": "mouse-pointer-click"}
TONS = {"arme": "arme", "desarme": "veille"}
JOURNAL_MAX = 15 * 60        # secondes notées par session
JOURNAUX_GARDES = 3


class Journal:
    """Note chaque image où une main est vue, pour comprendre après coup un geste raté.
    journal/session-*.csv ; seules les dernières sessions sont gardées."""

    MESURES = ("pincement", "pouce_majeur", "index_deplie")

    def __init__(self) -> None:
        import csv
        from .chemins import JOURNAL
        dossier = JOURNAL
        dossier.mkdir(parents=True, exist_ok=True)
        for vieux in sorted(dossier.glob("session-*.csv"))[:-(JOURNAUX_GARDES - 1) or None]:
            try:
                vieux.unlink()
            except OSError:
                pass
        self.chemin = dossier / f"session-{datetime.now():%Y%m%d-%H%M%S}.csv"
        self._f = open(self.chemin, "w", newline="", encoding="utf-8")
        self._w = csv.writer(self._f, delimiter=";")
        self._w.writerow(["t", "geste", "arme", "clic_attendu", *self.MESURES, "evenements"]
                         + [f"{c}{i}" for i in range(21) for c in "xy"])

    def noter(self, t: float, geste, arme: bool, clic: bool, points, evenements) -> None:
        if self._f.closed or points is None and not evenements:
            return
        if t > JOURNAL_MAX:
            self.fermer()
            return
        m = mesures(points) if points else {}
        self._w.writerow([f"{t:.3f}", geste.value, int(arme), int(clic),
                          *(f"{m[k]:.3f}" if k in m else "" for k in self.MESURES),
                          " ".join(f"{e.nom}:{e.geste}" for e in evenements if e.nom != "curseur"),
                          *(f"{v:.4f}" for pt in (points or []) for v in pt)])

    def fermer(self) -> None:
        if not self._f.closed:
            self._f.close()


class Service:
    def __init__(self, reglages: dict, sur_action=None, essai: bool = False) -> None:
        self.reglages = reglages
        self.sur_action = sur_action          # rappel(libellé, icône) pour le témoin flottant
        self.essai = essai
        self._fil: threading.Thread | None = None
        self._stop = threading.Event()
        self._verrou = threading.Lock()
        self._historique: deque[dict] = deque(maxlen=12)
        self._etat = self._etat_vide()

    # --- API (appelée depuis l'interface) ---
    def demarrer(self) -> None:
        if self._fil and self._fil.is_alive():
            return
        self._stop.clear()
        self._maj(ecoute=True, demarrage=True, erreur=None)
        self._fil = threading.Thread(target=self._boucle, name="gestes-camera", daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        self._stop.set()
        if self._fil:
            self._fil.join(timeout=3)
        self._fil = None
        self._maj(**self._etat_vide())

    def en_marche(self) -> bool:
        return bool(self._fil and self._fil.is_alive())

    def instantane(self) -> dict:
        with self._verrou:
            return {**self._etat, "historique": list(self._historique), "essai": self.essai}

    # --- interne ---
    @staticmethod
    def _etat_vide() -> dict:
        return {"ecoute": False, "demarrage": False, "camera": False, "arme": False, "attrape": False,
                "choix": False, "geste": "aucun", "progression": 0.0, "points": None, "profil": "Bureau", "erreur": None,
                "ips": 0}

    def _maj(self, **kw) -> None:
        with self._verrou:
            self._etat.update(kw)

    def _noter(self, geste: str | None, nom_ev: str, libelle: str) -> None:
        g = GESTES_PAR_ID.get(geste or "")
        nom = g["nom"] if g else {"arme": "Main ouverte", "desarme": "Inactivité", "clic": "OK"}.get(geste or nom_ev, "")
        icone = g["icone"] if g else ICONES.get(geste or nom_ev, "hand")
        maintenant = datetime.now()
        with self._verrou:
            dernier = self._historique[0] if self._historique else None
            # les gestes continus (volume…) donnent une rafale : on fusionne
            if dernier and dernier["libelle"] == libelle and time.time() - dernier["_t"] < 1.5:
                dernier.update(heure=maintenant.strftime("%H:%M:%S"), _t=time.time())
            else:
                self._historique.appendleft({"geste": nom, "libelle": libelle, "icone": icone,
                                             "heure": maintenant.strftime("%H:%M:%S"), "_t": time.time()})
        if self.sur_action:
            # l'armement et la veille ont leur couleur : on voit d'un coup d'œil si les gestes écoutent
            self.sur_action(libelle, icone, nom, TONS.get(nom_ev, ""))

    def _boucle(self) -> None:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

        from .actions import Executeur
        from .app import modele

        executeur = Executeur(essai=self.essai)
        cam = None
        journal = None
        try:
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_buffer=modele().read_bytes()),
                running_mode=RunningMode.VIDEO, num_hands=1,
                min_hand_detection_confidence=config.CONFIANCE_DETECTION,
                min_tracking_confidence=config.CONFIANCE_SUIVI)
            from .camera import ouvrir
            cam = ouvrir(config.CAMERA_INDEX)
            if cam is None:
                self._maj(demarrage=False, erreur="Caméra introuvable ou déjà utilisée par une autre application.")
                return
            self._maj(demarrage=False, camera=True)

            moteur = Moteur(actifs(self.reglages))
            try:
                journal = Journal()
            except OSError:
                journal = None
            profil = self.reglages["profils"][0]
            prochain_profil, t0, images, t_ips = 0.0, time.monotonic(), 0, time.monotonic()

            with HandLandmarker.create_from_options(options) as detecteur:
                from .camera import Horodateur
                horloge = Horodateur()
                while not self._stop.is_set():
                    ok, img = cam.read()
                    if not ok:
                        self._maj(erreur="La caméra ne répond plus.")
                        break
                    if config.MIROIR:
                        img = cv2.flip(img, 1)
                    t = time.monotonic() - t0
                    res = detecteur.detect_for_video(
                        mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)),
                        horloge.ms(t))

                    if t >= prochain_profil:   # réglages et profil relus deux fois par seconde
                        prochain_profil = t + 0.5
                        moteur.actifs = actifs(self.reglages)
                        profil = profil_actif(self.reglages["profils"], *appli_au_premier_plan())

                    points = [(lm.x, lm.y) for lm in res.hand_landmarks[0]] if res.hand_landmarks else None
                    clic = moteur.clic_attendu(t)
                    geste = classer(points, moteur.geste is Geste.PINCEMENT, clic) if points else Geste.AUCUN
                    paume = centre_paume(points) if points else None
                    evenements = moteur.mettre_a_jour(geste, paume, t, points[INDEX_BASE] if points else None)
                    if journal:
                        journal.noter(t, geste, moteur.arme, clic, points, evenements)

                    for ev in evenements:
                        if self.reglages["confort"].get("gaucher") and ev.nom in ("debut", "direction"):
                            ev.sens = -ev.sens
                        cle = "pointer" if ev.geste == "clic" else ev.geste
                        choix = choix_pour(self.reglages, profil, cle) if cle else None
                        libelle = executeur.executer(ev, choix)
                        if ev.nom == "direction" and (choix or {}).get("action") == "choisir_fenetre":
                            moteur.entrer_mode_choix(t)
                        if libelle:
                            self._noter(ev.geste, ev.nom, libelle)

                    images += 1
                    if time.monotonic() - t_ips >= 1:
                        ips, images, t_ips = images, 0, time.monotonic()
                    else:
                        ips = self._etat["ips"]
                    self._maj(arme=moteur.arme, attrape=moteur.attrape, choix=moteur.en_choix, geste=moteur.geste.value,
                              progression=round(moteur.progression, 2), profil=profil["nom"], ips=ips,
                              points=[(round(x, 3), round(y, 3)) for x, y in points] if points else None)
        except Exception as e:   # une erreur ne doit jamais laisser Alt enfoncé ni la caméra prise
            self._maj(erreur=f"Erreur : {e}")
        finally:
            executeur.relacher_tout()
            if journal:
                journal.fermer()
            if cam is not None:
                cam.release()
            self._maj(camera=False, arme=False, attrape=False, points=None, demarrage=False,
                      ecoute=False)
