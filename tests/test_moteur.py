from gestes_webcam import config
from gestes_webcam.geometrie import Geste
from gestes_webcam.moteur import Moteur, vers_ecran

PAUME = (0.5, 0.5)
PAS = 1 / 30


def jouer(m, geste, duree, t0, paume=PAUME, curseur=None):
    """Envoie le même geste pendant `duree` secondes à 30 images/s."""
    evs, t = [], t0
    while t < t0 + duree:
        evs += m.mettre_a_jour(geste, paume, t, curseur)
        t += PAS
    return evs, t


def noms(evs):
    return [(e.nom, e.geste, e.sens) if e.geste else e.nom for e in evs if e.nom != "curseur"]


def trajet(m, geste, t, depart, arrivee, images=10):
    """Déplace la paume en ligne droite de `depart` à `arrivee`."""
    evs = []
    for i in range(images + 1):
        f = i / images
        p = (depart[0] + (arrivee[0] - depart[0]) * f, depart[1] + (arrivee[1] - depart[1]) * f)
        evs += m.mettre_a_jour(geste, p, t)
        t += PAS
    return evs, t


def armer(m):
    evs, t = jouer(m, Geste.MAIN_OUVERTE, config.DUREE_ACTIVATION + 0.1, 0.0)
    assert noms(evs) == ["arme"] and m.arme
    return t


# --- armement ---------------------------------------------------------------

def test_rien_ne_part_tant_que_le_systeme_est_desarme():
    m = Moteur()
    evs, _ = jouer(m, Geste.POING, 2.0, 0.0)
    assert evs == [] and not m.arme


def test_desarmement_apres_inactivite():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.AUCUN, config.DUREE_ARMEMENT + 0.5, t)
    assert "desarme" in noms(evs) and not m.arme


# --- gestes tenus -----------------------------------------------------------

def test_poing_tenu_une_seule_fois():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.POING, 2.0, t)
    assert noms(evs) == [("maintien", "poing", 0)]


def test_geste_trop_court_ignore():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.POUCE_LEVE, config.DUREE_MAINTIEN / 2, t)
    assert evs == []


def test_pouce_baisse():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.POUCE_BAS, 1.0, t)
    assert noms(evs) == [("maintien", "pouce_bas", 0)]


def test_geste_desactive_ignore():
    m = Moteur(actifs={"pouce"})
    t = armer(m)
    evs, _ = jouer(m, Geste.POING, 1.0, t)
    assert evs == []


def test_main_ouverte_armee_ne_fait_rien():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.MAIN_OUVERTE, 2.0, t)
    assert evs == []


# --- balayage ---------------------------------------------------------------

def test_balayage_droite_puis_delai():
    m = Moteur()
    t = armer(m)
    evs, t = trajet(m, Geste.MAIN_OUVERTE, t, (0.5, 0.5), (0.8, 0.5))
    assert noms(evs) == [("direction", "balayage", 1)]
    evs2, _ = trajet(m, Geste.MAIN_OUVERTE, t, (0.8, 0.5), (0.5, 0.5))
    assert evs2 == []   # retour immédiat bloqué par le délai


def test_balayage_tolere_main_perdue_et_forme_changeante():
    m = Moteur()
    t = armer(m)
    evs = []
    for i in range(12):
        x = 0.50 + i * 0.02
        geste = Geste.MAIN_OUVERTE if i % 3 else Geste.AUCUN
        evs += m.mettre_a_jour(geste, None if i in (4, 5) else (x, 0.5), t)
        t += PAS
    assert ("direction", "balayage", 1) in noms(evs)


def test_index_pointe_qui_bouge_ne_balaye_pas():
    m = Moteur()
    t = armer(m)
    evs, _ = trajet(m, Geste.POINTER, t, (0.4, 0.5), (0.8, 0.5))
    assert not any(e.nom == "direction" for e in evs)


# --- attraper, glisser, lâcher ---------------------------------------------

def test_attraper_glisser_lacher():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.POING, 0.1, t)                   # on ferme la main
    evs, t = trajet(m, Geste.POING, t, (0.5, 0.5), (0.72, 0.5), images=12)
    assert noms(evs)[0] == ("debut", "attraper", 1)
    assert noms(evs).count(("direction", "attraper", 1)) == 2   # 0,22 - 0,06 de départ, par pas de 0,07
    assert m.attrape
    evs, _ = jouer(m, Geste.MAIN_OUVERTE, 0.4, t, paume=(0.72, 0.5))  # on rouvre
    assert noms(evs) == [("fin", "attraper", 0)] and not m.attrape


def test_attraper_ne_declenche_pas_lecture_pause():
    m = Moteur()
    t = armer(m)
    evs, t = trajet(m, Geste.POING, t, (0.5, 0.5), (0.7, 0.5))
    evs2, _ = jouer(m, Geste.POING, 1.0, t, paume=(0.7, 0.5))
    assert ("maintien", "poing", 0) not in noms(evs + evs2)


def test_attraper_lache_si_main_perdue():
    m = Moteur()
    t = armer(m)
    _, t = trajet(m, Geste.POING, t, (0.5, 0.5), (0.65, 0.5))
    assert m.attrape
    evs, _ = jouer(m, Geste.AUCUN, config.PERTE_MAX + 0.2, t, paume=None)
    assert ("fin", "attraper", 0) in noms(evs)


def test_poing_tenu_puis_deplace_ne_lance_pas_attraper():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.POING, 1.0, t)
    evs, _ = trajet(m, Geste.POING, t, (0.5, 0.5), (0.8, 0.5))
    assert not m.attrape and evs == []


# --- gestes continus --------------------------------------------------------

def test_pincer_et_monter_donne_des_crans():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.PINCEMENT, config.DEBUT_CONTINU + 0.05, t, paume=(0.5, 0.6))
    evs, _ = trajet(m, Geste.PINCEMENT, t, (0.5, 0.6), (0.5, 0.4))
    crans = sum(e.sens for e in evs if e.nom == "continu" and e.geste == "pincer")
    assert crans == int(0.2 / config.PAS_CONTINU)


def test_deux_doigts_vers_le_bas():
    m = Moteur()
    t = armer(m)
    evs, _ = trajet(m, Geste.DEUX_DOIGTS, t, (0.5, 0.4), (0.5, 0.6))
    assert sum(e.sens for e in evs if e.geste == "deux_doigts") < 0


# --- curseur et clic --------------------------------------------------------

def test_index_pointe_envoie_le_curseur():
    m = Moteur()
    t = armer(m)
    evs, _ = jouer(m, Geste.POINTER, 0.2, t, curseur=(0.3, 0.3))
    assert evs and {e.nom for e in evs} == {"curseur"}


def test_pincement_apres_pointer_est_un_clic():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.POINTER, 0.3, t, curseur=(0.3, 0.3))
    evs, _ = jouer(m, Geste.PINCEMENT, 0.5, t)
    assert noms(evs) == [("maintien", "clic", 0)]


def test_pas_de_rafale_de_clics():
    m = Moteur(actifs={"pointer"})
    t = armer(m)
    evs = []
    for _ in range(4):
        e, t = jouer(m, Geste.PINCEMENT, 0.3, t)
        evs += e
        _, t = jouer(m, Geste.POINTER, 0.05, t)
    assert noms(evs).count(("maintien", "clic", 0)) == 2


# --- outils -----------------------------------------------------------------

def test_filtre_1euro_lisse_le_tremblement_et_suit_le_mouvement():
    from gestes_webcam.souris import Filtre1Euro
    f = Filtre1Euro(coupure_min=1.0, beta=0.01)
    # doigt immobile qui tremble de ±6 px : le curseur bouge bien moins
    pos = [f.filtrer((500 + (6 if i % 2 else -6), 300), i / 30)[0] for i in range(60)]
    assert max(pos[30:]) - min(pos[30:]) < 4
    # mouvement franc de 1 500 px/s : le curseur suit avec peu de retard
    for i in range(60, 75):
        x, _ = f.filtrer((500 + (i - 60) * 50, 300), i / 30)
    assert x > 500 + 14 * 50 - 120


def test_vers_ecran_borne():
    assert vers_ecran((0.0, 1.0), 1920, 1080, zone=(0.2, 0.2, 0.8, 0.8)) == (0, 1079)


def test_pincer_tolere_des_images_perdues():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.PINCEMENT, config.DEBUT_CONTINU + 0.05, t, paume=(0.5, 0.6))
    evs = []
    for i in range(13):
        y = 0.6 - 0.2 * i / 12
        g = Geste.AUCUN if i % 4 == 3 else Geste.PINCEMENT   # le pincement « saute » une image sur quatre
        evs += m.mettre_a_jour(g, (0.5, y), t)
        t += PAS
    crans = sum(e.sens for e in evs if e.nom == "continu" and e.geste == "pincer")
    assert crans >= int(0.2 / config.PAS_CONTINU) - 1


def test_pincement_eclair_ne_change_pas_le_volume():
    # Mesuré : en bougeant librement, la main ressemble parfois 1 à 3 images à un pincement.
    m = Moteur()
    t = armer(m)
    evs, t = trajet(m, Geste.PINCEMENT, t, (0.5, 0.6), (0.5, 0.45), images=3)
    assert not [e for e in evs if e.nom == "continu"]


# --- mode Wiimote : choisir une fenêtre au doigt -----------------------------

def mode_choix():
    m = Moteur({"balayage", "poing", "pincer", "pouce"})   # « pointer » inactif hors mode
    t = armer(m)
    m.entrer_mode_choix(t)
    return m, t


def test_mode_choix_le_doigt_guide_la_souris():
    m, t = mode_choix()
    evs, _ = jouer(m, Geste.POINTER, 0.3, t, curseur=(0.4, 0.4))
    assert any(e.nom == "curseur" for e in evs)


def test_mode_choix_le_pincement_clique_et_termine():
    m, t = mode_choix()
    _, t = jouer(m, Geste.POINTER, 0.3, t, curseur=(0.4, 0.4))
    evs, t = jouer(m, Geste.PINCEMENT, 0.5, t)
    assert ("maintien", "clic", 0) in noms(evs)
    assert not [e for e in evs if e.nom == "continu"]       # pas de volume
    assert not m.en_choix


def test_mode_choix_poing_annule():
    m, t = mode_choix()
    evs, _ = jouer(m, Geste.POING, config.DUREE_MAINTIEN + 0.1, t)
    assert ("fin", "choix", 0) in noms(evs) and not m.en_choix
    assert ("maintien", "poing", 0) not in noms(evs)        # pas de pause en prime


def test_mode_choix_expire():
    m, t = mode_choix()
    evs, _ = jouer(m, Geste.AUCUN, config.DUREE_MODE_CHOIX + 0.2, t)
    assert ("fin", "choix", 0) in noms(evs) and not m.en_choix


def test_mode_choix_pas_de_balayage():
    m, t = mode_choix()
    evs, _ = trajet(m, Geste.MAIN_OUVERTE, t, (0.3, 0.5), (0.7, 0.5), images=8)
    assert not [e for e in evs if e.nom == "direction"]


def test_clic_attendu_juste_apres_avoir_pointe():
    m = Moteur()
    assert not m.clic_attendu(0.0)                 # pas armé : aucun clic possible
    t = 0.0
    while not m.arme:
        m.mettre_a_jour(Geste.MAIN_OUVERTE, (0.5, 0.5), t)
        t += 1 / 30
    assert not m.clic_attendu(t)                   # armé mais pas encore pointé
    m.mettre_a_jour(Geste.POINTER, (0.5, 0.5), t, (0.5, 0.5))
    assert m.clic_attendu(t + 0.5)
    assert not m.clic_attendu(t + 3.0)             # trop tard : le pincement redevient le volume


def test_clic_a_la_position_visee_avant_le_pincement(monkeypatch):
    from gestes_webcam import actions
    ex = actions.Executeur(essai=True)
    horloge = iter([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    monkeypatch.setattr(actions.time, "monotonic", lambda: next(horloge))
    for x in (100, 100, 100, 110, 130, 160):        # l'index se courbe : la souris glisse
        ex._traces.append((actions.time.monotonic(), x, 50))
    assert ex.position_visee() == (100, 50)


def test_defilement_plus_fin_que_le_volume():
    m = Moteur()
    t = armer(m)
    _, t = jouer(m, Geste.DEUX_DOIGTS, config.DEBUT_CONTINU + 0.05, t, paume=(0.5, 0.6))
    evs, _ = trajet(m, Geste.DEUX_DOIGTS, t, (0.5, 0.6), (0.5, 0.4))
    crans = sum(e.sens for e in evs if e.nom == "continu" and e.geste == "deux_doigts")
    assert crans == int(0.2 / config.PAS_DEFILEMENT) > int(0.2 / config.PAS_CONTINU)
