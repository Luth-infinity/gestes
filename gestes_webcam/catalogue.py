"""Catalogue des gestes, des actions et des profils par défaut.

Source unique : l'interface le lit pour construire ses listes, le moteur
et l'exécuteur s'en servent pour savoir quoi faire.
Chaque action a un type ; un geste ne propose que les actions de son type.
"""

# id -> (libellé, type)
ACTIONS = {
    # gestes tenus
    "lecture_pause": ("Lecture / pause", "maintien"),
    "valider": ("Valider (Entrée)", "maintien"),
    "annuler": ("Annuler (Échap)", "maintien"),
    "muet": ("Couper le son", "maintien"),
    "capture": ("Capture d'écran", "maintien"),
    "vue_taches": ("Vue des tâches", "maintien"),
    "afficher_bureau": ("Afficher le bureau", "maintien"),
    "diaporama": ("Lancer le diaporama", "maintien"),
    "ecran_noir": ("Écran noir (diaporama)", "maintien"),
    "raccourci": ("Raccourci personnalisé…", "maintien"),
    "lancer": ("Lancer une application…", "maintien"),
    # gestes directionnels
    "choisir_fenetre": ("Choisir une fenêtre au doigt", "direction"),
    "selecteur": ("Sélecteur de fenêtres", "direction"),
    "bureau_virtuel": ("Changer de bureau virtuel", "direction"),
    "fenetre": ("Fenêtre suivante / précédente", "direction"),
    "onglet": ("Onglet suivant / précédent", "direction"),
    "piste": ("Piste suivante / précédente", "direction"),
    "diapo": ("Diapo suivante / précédente", "direction"),
    # gestes continus
    "volume": ("Volume", "continu"),
    "defiler": ("Défiler la page", "continu"),
    "zoom": ("Zoom", "continu"),
    # curseur
    "curseur": ("Curseur et clic", "curseur"),
    # commun
    "rien": ("Ne rien faire", "*"),
}

GESTES = [
    {"id": "attraper", "nom": "Attraper, glisser, lâcher", "type": "direction", "icone": "grab",
     "desc": "Ferme la main, glisse à gauche ou à droite, rouvre pour choisir.", "action": "selecteur", "actif": False},
    {"id": "balayage", "nom": "Balayage", "type": "direction", "icone": "move-horizontal",
     "desc": "Main ouverte, mouvement franc d'un côté. Ouvre toutes les fenêtres : pointe, puis pince pour choisir.", "action": "choisir_fenetre", "actif": True},
    {"id": "poing", "nom": "Poing", "type": "maintien", "icone": "hand-fist",
     "desc": "Ferme le poing et tiens-le un court instant, sans bouger.", "action": "lecture_pause", "actif": True},
    {"id": "pincer", "nom": "Pincer et monter", "type": "continu", "icone": "audio-lines",
     "desc": "Pince pouce et index (un autre doigt détendu), puis monte ou descends.", "action": "volume", "actif": True},
    {"id": "pouce", "nom": "Pouce levé", "type": "maintien", "icone": "thumbs-up",
     "desc": "Pouce vers le haut, les autres doigts repliés.", "action": "valider", "actif": True},
    {"id": "pouce_bas", "nom": "Pouce baissé", "type": "maintien", "icone": "thumbs-down",
     "desc": "Pouce vers le bas, les autres doigts repliés.", "action": "annuler", "actif": True},
    {"id": "deux_doigts", "nom": "Deux doigts", "type": "continu", "icone": "chevrons-up-down",
     "desc": "Index et majeur tendus, monte ou descends pour faire défiler. Depuis l'index pointé, lève juste le majeur.", "action": "defiler", "actif": True},
    {"id": "pointer", "nom": "Index pointé + OK", "type": "curseur", "icone": "pointer",
     "desc": "Index levé : la souris suit ton doigt. Pince juste après pour cliquer.", "action": "curseur", "actif": True},
]
GESTES_PAR_ID = {g["id"]: g for g in GESTES}

PROFILS = [
    {"id": "bureau", "nom": "Bureau", "icone": "monitor", "actif": True, "defaut": True,
     "apps": [], "titres": [], "actions": {}},
    {"id": "presentation", "nom": "Présentation", "icone": "presentation", "actif": True, "defaut": False,
     "apps": ["powerpnt.exe", "acrord32.exe", "acrobat.exe"], "titres": [],
     "actions": {"balayage": {"action": "diapo"}, "poing": {"action": "ecran_noir"},
                 "pouce": {"action": "diaporama"}}},
    {"id": "media", "nom": "Média", "icone": "music-2", "actif": True, "defaut": False,
     "apps": ["spotify.exe", "vlc.exe"], "titres": ["YouTube", "Netflix"],
     "actions": {"balayage": {"action": "piste"}}},
]


def actions_pour(type_geste: str) -> list[str]:
    return [a for a, (_, t) in ACTIONS.items() if t in (type_geste, "*")]
