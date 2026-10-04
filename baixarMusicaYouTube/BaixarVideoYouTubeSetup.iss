#ifndef AppExecutable
  #define AppExecutable "dist\baixar_musica_qt.exe"
#endif

[Setup]
; Preserve the existing installer identity while changing the visible name.
AppId=Baixar Música YouTube
AppName=UIfor_yt-dlp
AppVersion=3.0.0
AppPublisher=Vinícius
LicenseFile=..\LICENSE
DefaultDirName={autopf}\BaixarMusicaYouTube
DefaultGroupName=UIfor_yt-dlp
OutputDir=Output
OutputBaseFilename=BaixarMusicaYouTube_Setup_v3
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico

[Files]
Source: "{#AppExecutable}"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "bin\licenses\*"; DestDir: "{app}\licenses\tools"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\UIfor_yt-dlp"; Filename: "{app}\baixar_musica_qt.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\UIfor_yt-dlp"; Filename: "{app}\baixar_musica_qt.exe"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\baixar_musica_qt.exe"; Description: "Abrir UIfor_yt-dlp"; Flags: nowait postinstall skipifsilent
