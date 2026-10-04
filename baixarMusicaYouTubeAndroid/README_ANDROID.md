# Baixar Música YouTube Android · base pública v3

Aplicativo Java com o backend `youtubedl-android` 0.18.1 e ferramentas nativas FFmpeg, FFprobe, Python e QuickJS. Mantém MP4, MP3, WEBM, MKV, GIF, WAV e playlists YouTube. Saídas em `Downloads/BaixarMusicaYouTube` pelo MediaStore.

## Ambiente

- JDK 17, AGP 9.4.0 e Gradle Wrapper 9.6.0 com checksum.
- compileSdk 36, targetSdk 35, minSdk 29 (Android 10+).
- applicationId e assinatura release existentes preservados.
- Bibliotecas do wrapper permanecem intactas; dependências transitivas são revisadas no Gradle do app.

Na raiz do repositório, configure JAVA_HOME para JDK 17 e ANDROID_HOME para o SDK, então rode `baixarMusicaYouTubeAndroid/build_android.ps1` no Windows ou `bash build_android.sh` dentro desta pasta no Linux. Consulte [Build](../docs/BUILD.md) para comandos completos, lint e verificação do APK.

O wrapper configura automaticamente QuickJS. O APK inclui EJS no backend empacotado. O app tenta atualizar yt-dlp no canal estável antes do download e mantém o fallback antigo se a atualização falhar. A versão realmente embutida e os limites da validação estão em [Validação](../docs/VALIDATION.md).

## Assinatura e publicação

APK debug não usa sua chave release. `build_android_release.ps1` mantém o fluxo local de assinatura; guarde `release-signing/` fora do Git. Este trabalho não executa release, instala em celular nem altera sua chave. APK compilado não prova download em aparelho real.

## IA e licença

Este app é produzido principalmente por IA com orientação humana; a história e a distinção em relação às bibliotecas estão no [README português](../README.md) e [English README](../README.en.md). Não há modelo de IA executando downloads. Código GPLv3, com avisos próprios das dependências; GPLv3 e avisos de terceiros entram nos assets do APK.
