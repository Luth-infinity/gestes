; Installateur Windows de Gestes : sortie dans empaqueter\sortie\Gestes-Setup-<version>.exe
; Compilé par construire.bat (Inno Setup 6).
#ifndef Version
  #define Version "0.1.0"
#endif

[Setup]
AppId={{6B0E2C1A-4F7D-4B8E-9E1C-7A3D5F2B9C41}
AppName=Gestes
AppVersion={#Version}
AppVerName=Gestes {#Version}
AppPublisher=Gestes
VersionInfoVersion={#Version}
VersionInfoDescription=Installation de Gestes
DefaultDirName={autopf}\Gestes
DefaultGroupName=Gestes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=sortie
OutputBaseFilename=Gestes-Setup-{#Version}
SetupIconFile=gestes.ico
UninstallDisplayIcon={app}\Gestes.exe
UninstallDisplayName=Gestes
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; L'app doit être fermée pour être mise à jour (même mutex que dans appli.py).
AppMutex=Gestes.Webcam.Instance
CloseApplications=yes

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "bureau"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "demarrage"; Description: "Lancer Gestes avec Windows (en arrière-plan, près de l'horloge)"; GroupDescription: "Démarrage :"; Flags: unchecked

[Files]
Source: "dist\Gestes\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gestes"; Filename: "{app}\Gestes.exe"
Name: "{group}\Désinstaller Gestes"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Gestes"; Filename: "{app}\Gestes.exe"; Tasks: bureau

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Gestes"; ValueData: """{app}\Gestes.exe"" --cache"; Tasks: demarrage; Flags: uninsdeletevalue
; Désinstallation : on retire aussi la clé posée par le réglage « Démarrer avec Windows » de l'app.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "Gestes"; Flags: dontcreatekey uninsdeletevalue

[Run]
Filename: "{app}\Gestes.exe"; Description: "Ouvrir Gestes maintenant"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Gestes\journal"
