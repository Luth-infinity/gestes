/**
 * Les textes du site, dans les deux langues.
 *
 * Tout ce qui se lit est ici : la vitrine ne contient pas une phrase en dur.
 * Les noms des gestes et des actions sont ceux de l'application
 * (gestes_webcam/catalogue.py) : même mot pour la même chose.
 */

export type Langue = 'fr' | 'en';

export type Geste = { nom: string; action: string; texte: string; icone: string };

export type Contenu = {
  meta: { title: string; description: string };
  nav: { gestes: string; versions: string; telecharger: string; langue: string };
  hero: { titre: [string, string]; texte: string; mention: string };
  scene: { poses: string[]; volume: string; webcam: string };
  gestes: { titre: string; texte: string; items: Geste[] };
  etapes: { titre: string; texte: string; items: [string, string][] };
  apercu: { legende: string };
  details: [string, string][];
  telecharger: {
    windows: string;
    mac: string;
    macIntel: string;
    toutes: string;
    version: string;
    titre: string;
    texte: string;
    configuration: string;
    signature: string;
  };
  changelog: { titre: string };
  pied: { suite: string; code: string; versions: string };
};

export const fr: Contenu = {
  meta: {
    title: 'Gestes · ta main pilote ton ordinateur',
    description:
      "Volume, pause, souris, défilement et fenêtres, d'un geste de la main devant la webcam. Gratuit, pour Windows et macOS, et rien ne quitte ta machine."
  },
  nav: { gestes: 'Les gestes', versions: 'Versions', telecharger: 'Télécharger', langue: 'Langue' },
  hero: {
    titre: ['Ta main devient', 'la télécommande.'],
    texte:
      "Monte le son en pinçant les doigts, mets en pause d'un poing, déplace la souris de l'index. Ta webcam suffit : aucun matériel en plus, et rien n'est envoyé sur internet.",
    mention: 'Windows et macOS · gratuit · tout reste sur ta machine'
  },
  scene: {
    poses: ['Gestes armés', 'Volume', 'Lecture / pause', 'Curseur et clic', 'Défiler la page'],
    volume: '+8 %',
    webcam: 'Webcam'
  },
  gestes: {
    titre: 'Des gestes courts, faciles à tenir.',
    texte:
      "Chaque geste se règle dans l'app : choisis son action, un raccourci clavier ou une application à lancer. Tu peux aussi le couper.",
    items: [
      { nom: 'Pincer et monter', action: 'Volume', texte: 'Pince pouce et index, puis monte ou descends la main.', icone: 'pince' },
      { nom: 'Poing', action: 'Lecture / pause', texte: 'Ferme le poing et tiens-le un court instant, sans bouger.', icone: 'poing' },
      { nom: 'Index pointé + OK', action: 'Curseur et clic', texte: 'Index levé : la souris suit ton doigt. Pince juste après pour cliquer.', icone: 'index' },
      { nom: 'Deux doigts', action: 'Défiler la page', texte: 'Index et majeur tendus, monte ou descends pour faire défiler.', icone: 'deux' },
      { nom: 'Balayage', action: 'Choisir une fenêtre au doigt', texte: "Un mouvement franc d'un côté montre toutes les fenêtres : pointe, puis pince pour choisir.", icone: 'balayage' },
      { nom: 'Pouce levé ou baissé', action: 'Valider · Annuler', texte: 'Pouce vers le haut ou vers le bas, les autres doigts repliés.', icone: 'pouce' }
    ]
  },
  etapes: {
    titre: 'Pas de geste lancé par erreur.',
    texte:
      "Gestes reste en veille tant que tu ne l'appelles pas : tu peux parler avec les mains devant l'écran sans rien déclencher.",
    items: [
      ['Montre ta main ouverte', 'Tiens-la moins d’une seconde : la pastille bleue « Gestes armés » apparaît.'],
      ['Fais ton geste', 'Volume, pause, souris, défilement… La pastille confirme chaque geste reconnu.'],
      ['Baisse la main', 'Après quelques secondes sans geste, tout se remet en veille. Ctrl + Alt + G coupe la caméra à tout moment.']
    ]
  },
  apercu: {
    legende: "La fenêtre de réglages. Une fois fermée, Gestes reste près de l'horloge, ou dans la barre des menus sur Mac."
  },
  details: [
    ['Ta caméra reste chez toi', "La main est repérée sur ta machine, image par image, puis l'image est oubliée. Aucune image enregistrée, aucune connexion à internet."],
    ['Un geste, une action par app', 'Les profils changent les actions selon l’application au premier plan : dans PowerPoint le balayage change de diapo, dans Spotify il passe à la piste suivante.'],
    ['Toujours une sortie', "Ctrl + Alt + G coupe la caméra depuis n'importe où, l'icône aussi. Souris dans un coin de l'écran : arrêt d'urgence de toutes les actions."],
    ['N’importe quelle webcam', 'Celle de ton portable suffit. Place-toi face à elle, la main à 40 à 80 cm, avec de la lumière de face plutôt que dans le dos.']
  ],
  telecharger: {
    windows: 'Télécharger pour Windows',
    mac: 'Télécharger pour Mac',
    macIntel: 'Mac Intel',
    toutes: 'Toutes les versions',
    version: 'Version',
    titre: 'Installe-le, montre ta main.',
    texte: "Installation en moins d'une minute, sans droits administrateur sur Windows. Sur Mac, glisse Gestes dans Applications.",
    configuration: 'Windows 10 ou 11 (64 bits), ou macOS 12 et plus · une webcam',
    signature:
      "L'application n'est signée par aucun éditeur : Windows peut afficher un avertissement SmartScreen (« Informations complémentaires » puis « Exécuter quand même »), et sur macOS il faut l'ouvrir la première fois par un clic droit puis « Ouvrir ». Le Mac demande ensuite l'accès à la caméra et à l'accessibilité, pour que les gestes puissent agir."
  },
  changelog: { titre: 'Ce qui a changé.' },
  pied: { suite: 'Les autres apps Luth', code: 'Code source', versions: 'Toutes les versions' }
};

export const en: Contenu = {
  meta: {
    title: 'Gestes · your hand runs your computer',
    description:
      'Volume, pause, cursor, scrolling and windows, with a hand gesture in front of your webcam. Free, for Windows and macOS, and nothing leaves your machine.'
  },
  nav: { gestes: 'Gestures', versions: 'Releases', telecharger: 'Download', langue: 'Language' },
  hero: {
    titre: ['Your hand becomes', 'the remote.'],
    texte:
      'Pinch to turn the volume up, make a fist to pause, point to move the cursor. Your webcam is all it takes: no extra hardware, and nothing is sent online.',
    mention: 'Windows and macOS · free · everything stays on your machine'
  },
  scene: {
    poses: ['Gestures armed', 'Volume', 'Play / pause', 'Cursor and click', 'Scroll the page'],
    volume: '+8 %',
    webcam: 'Webcam'
  },
  gestes: {
    titre: 'Short gestures, easy to hold.',
    texte:
      'Every gesture can be set in the app: pick its action, a keyboard shortcut or an app to launch. You can also turn it off.',
    items: [
      { nom: 'Pinch and raise', action: 'Volume', texte: 'Pinch thumb and index, then move your hand up or down.', icone: 'pince' },
      { nom: 'Fist', action: 'Play / pause', texte: 'Close your fist and hold it for a moment, without moving.', icone: 'poing' },
      { nom: 'Point + OK', action: 'Cursor and click', texte: 'Raise your index: the cursor follows it. Pinch right after to click.', icone: 'index' },
      { nom: 'Two fingers', action: 'Scroll the page', texte: 'Index and middle finger up, move up or down to scroll.', icone: 'deux' },
      { nom: 'Swipe', action: 'Pick a window by pointing', texte: 'A clear move to one side shows every window: point, then pinch to pick.', icone: 'balayage' },
      { nom: 'Thumb up or down', action: 'Confirm · Cancel', texte: 'Thumb up or down, the other fingers folded.', icone: 'pouce' }
    ]
  },
  etapes: {
    titre: 'No gesture by accident.',
    texte: "Gestes stays asleep until you call it: you can talk with your hands in front of the screen without setting anything off.",
    items: [
      ['Show an open hand', 'Hold it for under a second: the blue “Gestures armed” badge appears.'],
      ['Make your gesture', 'Volume, pause, cursor, scrolling… The badge confirms every gesture it recognises.'],
      ['Lower your hand', 'After a few seconds without a gesture, everything goes back to sleep. Ctrl + Alt + G turns the camera off at any time.']
    ]
  },
  apercu: {
    legende: 'The settings window. Once closed, Gestes stays next to the clock, or in the menu bar on a Mac.'
  },
  details: [
    ['Your camera stays home', 'Your hand is tracked on your machine, frame by frame, then the frame is dropped. No image is stored, nothing goes online.'],
    ['One gesture, one action per app', 'Profiles change actions based on the app in front: in PowerPoint a swipe changes slides, in Spotify it skips to the next track.'],
    ['Always a way out', 'Ctrl + Alt + G turns the camera off from anywhere, and so does the icon. Move the mouse into a screen corner to stop every action.'],
    ['Any webcam', "Your laptop's will do. Face it, keep your hand 40 to 80 cm away, with light in front of you rather than behind."]
  ],
  telecharger: {
    windows: 'Download for Windows',
    mac: 'Download for Mac',
    macIntel: 'Intel Mac',
    toutes: 'All releases',
    version: 'Version',
    titre: 'Install it, show your hand.',
    texte: 'Installs in under a minute, no admin rights needed on Windows. On a Mac, drag Gestes into Applications.',
    configuration: 'Windows 10 or 11 (64-bit), or macOS 12 and later · a webcam',
    signature:
      'The app is not signed by a publisher: Windows may show a SmartScreen warning ("More info" then "Run anyway"), and on macOS you need to open it the first time with a right-click then "Open". The Mac then asks for camera and accessibility access, so gestures can act.'
  },
  changelog: { titre: 'What changed.' },
  pied: { suite: 'Other Luth apps', code: 'Source code', versions: 'All releases' }
};
