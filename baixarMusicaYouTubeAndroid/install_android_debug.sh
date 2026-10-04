#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

bash build_android.sh

if ! command -v adb >/dev/null 2>&1; then
  echo "adb não encontrado no PATH." >&2
  exit 1
fi

if ! adb devices | grep -q $'\tdevice$'; then
  echo "Nenhum aparelho Android conectado/autorizado via adb." >&2
  exit 1
fi

adb install -r app/build/outputs/apk/debug/app-debug.apk
echo "APK instalado no aparelho conectado."
