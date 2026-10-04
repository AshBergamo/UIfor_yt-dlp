[Setup]
AppName=Baixar Música YouTube
AppVersion=3.0.0
AppPublisher=Vinícius
LicenseFile=..\LICENSE
DefaultDirName={autopf}\BaixarMusicaYouTube
DefaultGroupName=Baixar Música YouTube
OutputDir=Output
OutputBaseFilename=BaixarMusicaYouTube_Setup_v3
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico

[Files]
Source: "dist\baixar_musica_qt.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "bin\licenses\*"; DestDir: "{app}\licenses\tools"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Baixar Música YouTube"; Filename: "{app}\baixar_musica_qt.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Baixar Música YouTube"; Filename: "{app}\baixar_musica_qt.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\baixar_musica_qt.exe"; Description: "Abrir Baixar Música YouTube"; Flags: nowait postinstall skipifsilent
