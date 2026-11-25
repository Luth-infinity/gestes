import json

from gestes_webcam import config, reglages as reg
from gestes_webcam.actions import _precedent, vers_pyautogui
from gestes_webcam.catalogue import ACTIONS, GESTES, actions_pour
from gestes_webcam.profils import choix_pour, profil_actif


def test_chaque_geste_a_une_action_par_defaut_compatible():
    for g in GESTES:
        assert g["action"] in actions_pour(g["type"])


def test_charger_fichier_absent_donne_les_defauts(tmp_path):
    r = reg.charger(tmp_path / "absent.json")
    assert r == reg.nettoyer(reg.defauts())


def test_aller_retour_et_fusion_avec_les_defauts(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"gestes": {"poing": {"actif": False}}, "inconnu": 1}), encoding="utf-8")
    r = reg.charger(f)
    assert r["gestes"]["poing"] == {"actif": False, "action": "lecture_pause", "param": None}
    assert r["gestes"]["pouce"]["actif"] is True        # clé absente du fichier -> défaut
    reg.enregistrer(r, f)
    assert reg.charger(f)["gestes"]["poing"]["actif"] is False


def test_action_incompatible_remplacee():
    r = reg.defauts()
    r["gestes"]["poing"]["action"] = "volume"            # un geste tenu ne peut pas régler le volume
    r["gestes"]["fantome"] = {"actif": True, "action": "rien"}
    r = reg.nettoyer(r)
    assert r["gestes"]["poing"]["action"] == "lecture_pause" and "fantome" not in r["gestes"]


def test_appliquer_confort():
    r = reg.defauts()
    r["confort"].update(maintien=0.9, lissage=0.8)
    reg.appliquer(r)
    assert config.DUREE_MAINTIEN == 0.9 and abs(config.COUPURE_MIN - 0.9) < 1e-9
    reg.appliquer(reg.defauts())


def test_profil_par_application_et_par_titre():
    profils = reg.defauts()["profils"]
    assert profil_actif(profils, "powerpnt.exe", "Diapo")["id"] == "presentation"
    assert profil_actif(profils, "msedge.exe", "Musique - YouTube")["id"] == "media"
    assert profil_actif(profils, "notepad.exe", "Sans titre")["id"] == "bureau"


def test_profil_desactive_ignore():
    profils = reg.defauts()["profils"]
    profils[1]["actif"] = False
    assert profil_actif(profils, "powerpnt.exe", "")["id"] == "bureau"


def test_choix_du_profil_sinon_de_base():
    r = reg.defauts()
    pres = r["profils"][1]
    assert choix_pour(r, pres, "balayage")["action"] == "diapo"
    assert choix_pour(r, pres, "pincer")["action"] == "volume"


def test_touches_et_libelles():
    assert vers_pyautogui(["Ctrl", "Maj", "ArrowLeft", "K"]) == ["ctrl", "shift", "left", "k"]
    assert _precedent(ACTIONS["piste"][0]) == "Piste précédente"


def test_balayage_change_d_application_par_defaut():
    from gestes_webcam.catalogue import GESTES_PAR_ID
    assert GESTES_PAR_ID["balayage"]["action"] in ("fenetre", "choisir_fenetre")


def test_balayage_ouvre_le_choix_de_fenetre_et_attraper_coupe():
    from gestes_webcam.catalogue import GESTES_PAR_ID
    assert GESTES_PAR_ID["balayage"]["action"] == "choisir_fenetre"
    assert GESTES_PAR_ID["attraper"]["actif"] is False   # gênait la pause au poing


def test_executeur_choix_de_fenetre():
    from gestes_webcam.actions import Executeur
    from gestes_webcam.moteur import Evenement
    ex, appels = Executeur(), []
    class Espion:
        def __getattr__(self, n): return lambda *a, **k: appels.append((n, a))
    ex.pg = Espion()
    ex.executer(Evenement("direction", "balayage", -1), {"action": "choisir_fenetre"})
    ex.executer(Evenement("fin", "choix"), None)
    from gestes_webcam.plateforme import RACCOURCIS
    assert appels == [("hotkey", RACCOURCIS["choisir_fenetre"]), ("press", ("esc",))]


def test_mode_wiimote_actif_partout_par_defaut():
    from gestes_webcam.catalogue import GESTES_PAR_ID
    assert GESTES_PAR_ID["pointer"]["actif"] is True
