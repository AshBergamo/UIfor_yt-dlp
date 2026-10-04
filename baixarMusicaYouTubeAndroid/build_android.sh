#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -z "${ANDROID_HOME:-}" ] && [ -d "$HOME/Android/Sdk" ]; then
  export ANDROID_HOME="$HOME/Android/Sdk"
  export ANDROID_SDK_ROOT="$ANDROID_HOME"
fi

if [ ! -f "./gradlew" ]; then
  echo "gradlew não encontrado ou sem permissão de execução. Abra esta pasta no Android Studio ou adicione o Gradle Wrapper." >&2
  exit 1
fi

JAVA_BIN="${JAVA_HOME:+$JAVA_HOME/bin/}java"
if ! "$JAVA_BIN" -version 2>&1 | grep -q 'version "17\.'; then
  echo "Este build usa JDK 17. Configure JAVA_HOME." >&2
  exit 1
fi
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-$(cd .. && pwd)/work/gradle}"
bash ./gradlew assembleDebug

APK="app/build/outputs/apk/debug/app-debug.apk"
entries="$(unzip -Z1 "$APK")"
for entry in \
  "lib/arm64-v8a/libffmpeg.so" \
  "lib/arm64-v8a/libpython.so" \
  "lib/arm64-v8a/libqjs.so"
do
  if ! grep -Fxq "$entry" <<< "$entries"; then
    echo "APK gerado sem dependência obrigatória: $entry" >&2
    exit 1
  fi
done

echo "APK gerado em: $APK"
echo "Verificação OK: FFmpeg/yt-dlp Android encontrados no APK."
