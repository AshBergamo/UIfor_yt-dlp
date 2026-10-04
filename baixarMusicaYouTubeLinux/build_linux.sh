#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 não encontrado. Instale Python 3 e python3-venv." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1 && [ ! -x "./ffmpeg" ] && [ ! -x "./bin/ffmpeg" ]; then
  echo "ffmpeg não encontrado. Instale pelo gerenciador da distro ou coloque um binário Linux chamado ./ffmpeg." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r ../requirements-build.txt
python -m PyInstaller --clean --noconfirm baixar_musica_qt_linux.spec

mkdir -p Output
PACKAGE_DIR="Output/baixar-musica-youtube-linux-v3"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"
cp dist/baixar_musica_qt "$PACKAGE_DIR/"
cp install_linux.sh README_LINUX.md pixil-frame-0.png "$PACKAGE_DIR/"
cp ../LICENSE ../THIRD_PARTY_NOTICES.md "$PACKAGE_DIR/"
cp -r bin/licenses "$PACKAGE_DIR/licenses"
tar -C Output -czf Output/baixar-musica-youtube-linux-v3.tar.gz baixar-musica-youtube-linux-v3

echo "Build concluído:"
echo "  Executável: dist/baixar_musica_qt"
echo "  Pacote:     Output/baixar-musica-youtube-linux-v3.tar.gz"
