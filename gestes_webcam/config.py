"""Réglages du prototype. Tout ce qui se règle à l'usage est ici."""

# --- Caméra ---
CAMERA_INDEX = 0          # 0 = webcam par défaut
MIROIR = True             # image retournée : ta droite = droite de l'écran

# --- Suivi MediaPipe ---
CONFIANCE_DETECTION = 0.7
CONFIANCE_SUIVI = 0.6

# --- Reconnaissance (valeurs relatives à la taille de la main) ---
RATIO_DOIGT_TENDU = 1.10      # bout plus loin du poignet que l'articulation x ce ratio
POUCE_ECARTE = 0.55           # distance bout du pouce / base de l'index
POUCE_AU_DESSUS = 0.30        # pouce levé : bout au-dessus de la base de l'index
# Seuils mesurés sur l'enregistrement du 24/11/2026 (journal/gestes-*.csv)
SEUIL_PINCEMENT = 0.35        # distance pouce / index (pincé : 0,07 à 0,26 ; main ouverte : 1,0)
POUCE_LOIN_DU_MAJEUR = 0.40   # pouce / articulation du majeur (poing : 0,13 ; pincement : 0,55 à 0,9)
INDEX_DEPLIE_PINCEMENT = 0.08 # bout / base de l'index (poing : 0,03 à 0,08 ; pincement : 0,1 à 0,3)
SEUIL_PINCEMENT_TENU = 0.45   # une fois pincé, tolérance plus large pendant que la main bouge
TOLERANCE_PINCEMENT = 0.30   # secondes : un pincement perdu un instant ne coupe pas le volume
# Juste après avoir pointé, le pincement sert à cliquer : on le reconnaît plus facilement.
# En passant de l'index pointé au pincement, le pouce part du majeur replié et l'index se courbe.
# Sur le vrai poing, ces valeurs ne donnent toujours aucun faux pincement (0 % des images).
SEUIL_PINCEMENT_CLIC = 0.42
POUCE_LOIN_DU_MAJEUR_CLIC = 0.25
RECUL_CLIC = 0.25             # secondes : on clique là où pointait le doigt juste avant de pincer

# --- Fiabilité (secondes) ---
DUREE_ACTIVATION = 0.8        # main ouverte tenue pour armer le système
DUREE_MAINTIEN = 0.6          # poing, pouce levé, main ouverte (une fois armé)
DUREE_PINCEMENT = 0.25        # le clic doit rester vif
DELAI_ENTRE_CLICS = 0.6       # coupe les rafales de clics
DUREE_ARMEMENT = 6.0          # le système se désarme après ce délai sans geste
SEUIL_IMMOBILE = 0.06         # déplacement max de la main pendant un maintien

# --- Balayage ---
FENETRE_BALAYAGE = 0.50       # secondes observées
DISTANCE_BALAYAGE = 0.15      # part de la largeur de l'image à parcourir
DELAI_ENTRE_BALAYAGES = 1.0
ANTI_RETOUR = 1.5             # sens inverse ignoré ce délai après un balayage (retour de la main)
BLOQUANTS_MIN = 2             # images de pincement, index… nécessaires pour annuler un balayage

# --- Attraper, glisser, lâcher ---
SEUIL_ATTRAPER = 0.06         # déplacement du poing qui lance « attraper »
PAS_ATTRAPER = 0.07           # distance pour passer à la fenêtre suivante
LACHER = 0.15                 # main rouverte depuis ce délai = on lâche
PERTE_MAX = 0.5               # main perdue plus longtemps = on lâche
ATTRAPER_MAX = 10.0           # sécurité : on lâche toujours au bout de ce délai

# --- Gestes continus (volume, défilement) ---
PAS_CONTINU = 0.035           # hauteur d'image pour un cran
PAS_DEFILEMENT = 0.012        # défilement : crans fins, la page suit la main en douceur
DELTA_DEFILEMENT = 40         # un tiers de cran de molette (120) par pas : défilement fin
DEBUT_CONTINU = 0.3           # secondes de pincement tenu avant que le volume réagisse (écarte les éclairs)

# --- Curseur (index pointé) ---
DUREE_MODE_CHOIX = 12.0       # vue des fenêtres : annulée (Échap) après ce délai sans choix
CURSEUR_ACTIF = True
ZONE_CURSEUR = (0.2, 0.15, 0.8, 0.75)   # x0, y0, x1, y1 de l'image -> tout l'écran
# Filtre 1 € : coupure basse = doigt presque immobile très lissé ; beta = réactivité quand il bouge vite
COUPURE_MIN = 1.35            # Hz, suit le réglage « Lissage » (plus bas = plus lisse)
BETA_CURSEUR = 0.012
SUIVI_GLISSEMENT = 0.35       # part du chemin faite à chaque pas de 8 ms entre deux images
