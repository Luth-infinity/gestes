# Gestes webcam · Contrôle du PC

Prototype : la webcam reconnaît quelques gestes de la main et déclenche des actions sur Windows 11.
Python, MediaPipe Hands (21 points par main), règles géométriques simples, PyAutoGUI pour les actions.

## Lancer

- **`lancer.bat`** : l'app. Fenêtre de réglages + icône près de l'horloge. La croix range l'app, elle continue d'écouter.
  `lancer.bat --essai` : même app, mais aucune action n'est envoyée au PC.
- **`essai.bat`** : mode diagnostic avec la vidéo, le squelette de la main et un journal CSV dans `journal/` pour régler les seuils.

Le premier lancement crée l'environnement `.venv` (Python 3.12) et télécharge le modèle de main (7 Mo).
**Ctrl + Alt + G** active ou coupe l'écoute partout. Arrêt d'urgence : souris dans un coin de l'écran.

## Gestes

La **main ouverte tenue une seconde** arme les gestes ; ils se remettent en veille après quelques secondes sans geste.

| Geste | Famille | Action par défaut |
|---|---|---|
| Attraper, glisser, lâcher | directionnel | Sélecteur de fenêtres (Alt maintenu) |
| Balayage | directionnel | Fenêtre suivante / précédente (Alt+Tab) |
| Poing tenu | tenu | Lecture / pause |
| Pincer et monter | continu | Volume |
| Pouce levé / baissé | tenu | Valider / Annuler |
| Deux doigts (désactivé) | continu | Défiler |
| Index pointé + OK (désactivé) | curseur | Curseur et clic |

Chaque geste propose les actions de sa famille, plus un raccourci clavier personnalisé ou le lancement d'une application.
Les **profils** changent ces actions selon l'application au premier plan (Présentation, Média, ou les tiens).

Réglages enregistrés dans `%APPDATA%\Gestes\reglages.json`.

## Structure

```
gestes.pyw            point d'entrée de l'app (sans console)
gestes_webcam/
  geometrie.py        points de la main -> geste
  moteur.py           armement, maintien, balayage, attraper, gestes continus
  catalogue.py        gestes, actions, profils par défaut
  actions.py          exécution clavier / souris / média
  reglages.py         lecture, écriture, application des réglages
  profils.py          application au premier plan -> profil
  service.py          fil caméra en arrière-plan
  appli.py            fenêtre pywebview, icône, raccourci global, témoin flottant
  ui/                 interface (HTML/CSS, style Clavier custom)
  app.py              mode diagnostic (essai.bat)
tests/                pytest, sans caméra
```

Tests : `.venv\Scripts\python.exe -m pytest`

## Limites connues

- Le calibrage guidé n'est pas encore fait : la page l'annonce.
- Les caméras sont listées « Caméra 1, 2… » sans leur nom réel.
- MediaPipe ne sait pas ouvrir un fichier dont le chemin contient un accent : le modèle est chargé en mémoire.
- Les seuils viennent de mains synthétiques ; ils seront à ajuster après un essai réel avec la webcam.

## Empaqueter et publier

- **Windows, en local** : `empaqueter\construire.bat` lance les tests, puis construit `Gestes.exe` (PyInstaller, `empaqueter/gestes.spec`)
  et l'installateur `empaqueter\sortie\Gestes-Setup-<version>.exe` (Inno Setup 6, `empaqueter/installeur.iss`), sans droits admin.
- **macOS** : `Gestes.app` et les `.dmg` (Apple Silicon et Intel) se construisent sur GitHub, dans le workflow `Release`.
  Code propre à chaque système : `gestes_webcam/plateforme.py`. Sur Mac, l'app demande les autorisations Caméra et Accessibilité.
- `Gestes --verifier` : charge tout (modèle, interface, système) sans caméra ni fenêtre, puis quitte (0 = OK). Le workflow l'utilise.
- `empaqueter/diagnostic.spec` : même empaquetage en console, qui teste pas à pas modèle, caméra et détection.
- Une fois installée, l'app écrit son journal dans `%LOCALAPPDATA%\Gestes\journal` (Windows) ou `~/Library/Application Support/Gestes` (macOS).

### Publier une version

1. Monter la version dans `gestes_webcam/__init__.py` (`0.x.y`, jamais en arrière), commit, push.
2. `gh release create vX.Y.Z --draft --title vX.Y.Z --notes-file notes.md` : notes en français, puis `## English`.
3. `git tag vX.Y.Z && git push origin vX.Y.Z` : le workflow joint `Gestes-Setup-X.Y.Z.exe`, `Gestes-X.Y.Z-arm64.dmg`,
   `Gestes-X.Y.Z-x64.dmg`, puis publie la release. Suivre avec `gh run watch`.
4. Le site (`site/`) lit les releases : téléchargements et « Ce qui a changé » se mettent à jour seuls (10 min de cache).

Signature : les builds ne sont pas signés. Sur macOS, le premier lancement demande un clic droit → « Ouvrir » ;
sur Windows, SmartScreen affiche un avertissement.
