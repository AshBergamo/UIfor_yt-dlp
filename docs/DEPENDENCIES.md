# Dependências / Dependencies

## Versões diretas desta base

| Componente | Versão |
| --- | --- |
| Python desktop (baseline) | 3.11 |
| PySide6 | 6.11.2 |
| yt-dlp + extras default | 2026.08.19 |
| PyInstaller | 6.22.3 |
| Android Gradle Plugin | 9.4.0 |
| Gradle | 9.6.0 |
| JDK Android | 17 |
| compileSdk / targetSdk / minSdk | 36 / 35 / 29 |
| youtubedl-android library / ffmpeg | 0.18.1 |

As versões resolvidas durante a validação e a revisão das dependências transitivas serão registradas aqui. Não usar `pip freeze` do Windows como lock universal para Linux: existem diferenças de plataforma. Os requisitos diretos compartilhados ficam na raiz; dependências de build ficam separadas.

FFmpeg/FFprobe e Deno são ferramentas externas, não pacotes Python. O bootstrap confere os arquivos baixados por SHA256 e registra versões em `bin/licenses/tools-versions.json`, excluído do Git. Linux usa a dupla FFmpeg da distribuição. O Android conserva as ferramentas nativas fornecidas pelo wrapper, com revisão específica de compatibilidade EJS.

## Verificado em 2026-10-04 — Windows / Python 3.11.9

Pacotes instalados em ambiente virtual novo; `pip check` passou. Versões resolvidas deste ambiente, sem tratá-las como lock universal Linux:

```text
altgraph==0.17.5
brotli==1.2.0
certifi==2026.7.22
charset-normalizer==3.5.2
idna==3.20
mutagen==1.48.1
packaging==26.3
pefile==2024.8.26
pycryptodomex==3.23.0
pyinstaller==6.22.3
pyinstaller-hooks-contrib==2026.8
PySide6==6.11.2
PySide6_Addons==6.11.2
PySide6_Essentials==6.11.2
pywin32-ctypes==0.2.3
requests==2.34.2
shiboken6==6.11.2
urllib3==2.8.0
websockets==17.2
yt-dlp==2026.8.19
yt-dlp-ejs==0.8.0
```

Ferramentas conferidas por SHA256: **FFmpeg 9.0.2**, **FFprobe 9.0.2** (Gyan essentials) e **Deno 2.9.7**. O bootstrap consulta a release estável corrente; builds futuros devem registrar o manifesto gerado e repetir a validação se essas versões mudarem. SHA256 dos arquivos nesta execução:

```text
ffmpeg archive: 60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba
deno archive: a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238
```

## Android — revisão transitiva

O wrapper 0.18.1 foi preservado. O Gradle do aplicativo atualiza e alinha as seguintes dependências, sem editar código de terceiros:

| Componente | Antes | Resolvido nesta base |
| --- | --- | --- |
| Jackson databind/core/annotations | 2.11.1 | BOM 2.22.3 (versões dos módulos conforme BOM) |
| Commons IO | 2.5 | 2.22.0 |
| Commons Compress | 1.12 | 1.28.0 |
| AndroidX AppCompat | 1.4.2 | 1.7.1 |
| AndroidX Core / Core KTX | 1.8.0 | 1.17.0 |

As versões AndroidX foram escolhidas para compileSdk 36; não são uma declaração de que sejam a versão mais nova de todas as linhas. Kotlin stdlib resolveu em 2.2.10 pelo ambiente de build. O APK contém yt-dlp **2025.11.12** como fallback, com EJS; a tentativa de atualização no app usa o canal estável, uma vez por processo, antes da primeira consulta de metadados pelo backend ou download. Inicialização/atualização são serializadas e compartilhadas pelas duas operações. A prévia oEmbed do YouTube não precisa iniciar esse backend. O wrapper passa `--js-runtimes quickjs:<caminho nativo>` automaticamente (conferido no artefato da biblioteca). Não duplicamos essa configuração. A expansão de fontes preserva as versões das bibliotecas desta base.

Commons Compress 1.12 precedia correções de ZIP/TAR publicadas pelo Apache. A atualização evita manter essa base antiga; isso não comprova explorabilidade anterior no app nem constitui auditoria completa. Fontes: [Compress](https://commons.apache.org/proper/commons-compress/security.html), [Commons IO](https://commons.apache.org/proper/commons-io/security.html), [Maven Central](https://central.sonatype.com/artifact/io.github.junkfood02.youtubedl-android/library).

AGP/Gradle, SDK e JDK são os valores aprovados na tabela, não os máximos anunciados para todas as plataformas. targetSdk 35 foi preservado deliberadamente. Lint informa avisos de versões mais novas e de recursos/tradução, sem erros no build validado; migração de targetSdk e tradução da UI são trabalhos separados.

English: these are measured resolved versions, not a cross-platform lock. Desktop tools are verified by SHA256 and their exact versions are recorded. Android retains the wrapper and bundled older yt-dlp fallback while upgrading compatible transitive libraries. Build/lint success does not prove execution on a physical phone.
