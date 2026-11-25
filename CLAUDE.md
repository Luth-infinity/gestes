# Gestes webcam · Contrôle du PC

Objectif : un prototype qui utilise la webcam pour reconnaître des gestes de la main et déclencher des actions sur le PC (Windows 11). Pas de bras robot ni de matériel en plus : une simple webcam et un script.

Inspiration : une vidéo X de Ronald van Loon (https://x.com/Ronald_vanLoon/status/2124569368948351015) qui montre un contrôle par gestes avec un bras robot qui bouge l'écran. On veut une version moins poussée, centrée sur les gestes qui déclenchent des actions.

Pile technique envisagée : Python + MediaPipe Hands (21 points par main) pour le suivi, règles simples pour reconnaître les gestes, pyautogui / pynput (ou AutoHotkey) pour les actions clavier, souris, média et fenêtres.

Gestes retenus pour le départ (les plus fiables) :
- Poing fermé = pause média
- Main ouverte (paume face à la caméra) = lecture, et sert aussi de geste d'activation
- Pouce levé = valider
- Balayage gauche/droite = changer de fenêtre ou de bureau virtuel
- Pincement pouce + index = clic

Règles de fiabilité : tenir le geste 0,5 à 1 s avant de déclencher, un geste d'activation qui arme le système, 4 à 6 gestes au maximum, délai entre deux balayages, lissage du curseur, bonne lumière de face, main à 40 à 80 cm de la caméra. Gestes de profil ou trop proches les uns des autres à éviter. Prévoir des gestes courts pour limiter la fatigue du bras.

## Publication (comme les autres outils Luth)

- Dépôt public `Luth-infinity/gestes`. Site Next.js bilingue dans `site/`, en ligne sur https://gestes-luth.vercel.app (projet Vercel `gestes-luth`, déploiement à la main : `cd site && vercel --prod`, puis vérifier l'alias).
- Release : voir « Publier une version » dans le README. Le workflow `.github/workflows/release.yml` construit l'installateur Windows (PyInstaller + Inno Setup) et les `.dmg` macOS (arm64 et x64, signature ad hoc, sans notarisation).
- Versions en `0.x.y`, jamais en arrière. Notes de release : français d'abord, puis `## English` (le site et notion-sync coupent à cet endroit).
- Code propre à Windows ou macOS : uniquement dans `gestes_webcam/plateforme.py` (et les deux classes de témoin dans `appli.py`). La version Mac n'a jamais été essayée sur un vrai Mac.
