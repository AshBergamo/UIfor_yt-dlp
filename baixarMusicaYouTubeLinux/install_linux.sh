#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_ID="baixar-musica-youtube"
APP_NAME="UIfor_yt-dlp"
SOURCE_BIN="${1:-dist/baixar_musica_qt}"
INSTALL_DIR="${HOME}/.local/opt/${APP_ID}"
BIN_DIR="${HOME}/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
APPLICATIONS_DIR="${DATA_HOME}/applications"
ICON_DIR="${DATA_HOME}/icons/hicolor/256x256/apps"

if [ ! -f "$SOURCE_BIN" ] && [ -f "./baixar_musica_qt" ]; then
  SOURCE_BIN="./baixar_musica_qt"
fi

if [ ! -f "$SOURCE_BIN" ]; then
  echo "Executável não encontrado em ${SOURCE_BIN}. Rode ./build_linux.sh primeiro." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$APPLICATIONS_DIR" "$ICON_DIR"

cp "$SOURCE_BIN" "${INSTALL_DIR}/baixar_musica_qt"
chmod +x "${INSTALL_DIR}/baixar_musica_qt"
for notice in LICENSE THIRD_PARTY_NOTICES.md; do
  if [ -f "$notice" ]; then
    cp "$notice" "$INSTALL_DIR/"
  elif [ -f "../$notice" ]; then
    cp "../$notice" "$INSTALL_DIR/"
  fi
done
if [ -d "licenses" ]; then
  cp -r licenses "$INSTALL_DIR/"
elif [ -d "bin/licenses" ]; then
  cp -r bin/licenses "$INSTALL_DIR/"
fi

cp pixil-frame-0.png "${ICON_DIR}/${APP_ID}.png"
ln -sf "${INSTALL_DIR}/baixar_musica_qt" "${BIN_DIR}/${APP_ID}"

cat > "${APPLICATIONS_DIR}/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=${INSTALL_DIR}/baixar_musica_qt
Icon=${APP_ID}
Categories=AudioVideo;Network;
Terminal=false
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

echo "Instalado em ${INSTALL_DIR}/baixar_musica_qt"
echo "Atalho criado em ${APPLICATIONS_DIR}/${APP_ID}.desktop"
echo "Comando opcional: ${APP_ID}"
