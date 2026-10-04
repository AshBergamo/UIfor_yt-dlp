# Build e distribuição / Build and distribution

Execute os comandos a partir da raiz, salvo indicação contrária. A primeira instalação precisa de internet. Os builds não publicam releases e não criam commits.

## Desktop Windows

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/setup_tools.py --output-dir baixarMusicaYouTube/bin
powershell -ExecutionPolicy Bypass -File baixarMusicaYouTube/build_windows.ps1
.\.venv\Scripts\python.exe scripts/check_bundle.py
.\.venv\Scripts\python.exe scripts/check_windows_ui.py
```

Saída: `baixarMusicaYouTube/dist/baixar_musica_qt.exe`. Os specs incluem ícones, ferramentas, EJS, licenças, o catálogo compartilhado `resources/sources.json` e os módulos de fontes/consulta de metadados; **nunca cookies**. Qt usa os hooks do PyInstaller para coletar módulos necessários, sem copiar toda a árvore QML.

A janela, os atalhos e o instalador agora mostram **UIfor_yt-dlp**. Os nomes de arquivos, diretórios e identidades anteriores foram preservados. O verificador também exige QtNetwork e um backend HTTPS para as miniaturas opcionais.

O helper isola a busca de DLLs Windows durante o build, evitando versões incompatíveis de ferramentas externas no PATH. Ao alterar essa configuração ou reaproveitar um cache antigo, use `--clean` no comando PyInstaller. Confira a abertura da janela do EXE; um processo ativo, sozinho, pode ser apenas um diálogo de erro. As novas fontes consultam metadados em um processo cancelável, com comunicação local Qt; o EXE sem console também usa esse caminho, sem depender de stdout.

Para gerar o instalador, após conferir o executável, use Inno Setup 6:

```powershell
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' baixarMusicaYouTube/BaixarVideoYouTubeSetup.iss
```

Saída: `baixarMusicaYouTube/Output/BaixarMusicaYouTube_Setup_v3.3.exe`. O instalador acompanha a GPLv3 e os avisos das ferramentas. Binários locais antigos não são evidência de funcionamento do novo fonte.

## Desktop Linux

Instale FFmpeg/FFprobe e requisitos Qt da distribuição, então:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python scripts/setup_tools.py --system-ffmpeg --output-dir baixarMusicaYouTubeLinux/bin
cd baixarMusicaYouTubeLinux
bash build_linux.sh
cd ..
.venv/bin/python scripts/check_bundle.py
```

O script cria seu ambiente de build Linux, executável e `.tar.gz` em `baixarMusicaYouTubeLinux/Output/`. A instalação por `install_linux.sh` é por usuário, sem sudo. PyInstaller não faz cross-build Windows → Linux. Bibliotecas do sistema/glibc limitam a portabilidade; testar o pacote no sistema de destino.

### Build Windows com o aplicativo aberto

Para gerar uma versão separada sem substituir o EXE que está em uso:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath baixarMusicaYouTube/dist/v3.3 --workpath baixarMusicaYouTube/build baixarMusicaYouTube/baixar_musica_qt.spec
.\.venv\Scripts\python.exe scripts/check_bundle.py --executable baixarMusicaYouTube/dist/v3.3/baixar_musica_qt.exe
.\.venv\Scripts\python.exe scripts/check_windows_ui.py --executable baixarMusicaYouTube/dist/v3.3/baixar_musica_qt.exe
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' "/DAppExecutable=$((Resolve-Path 'baixarMusicaYouTube/dist/v3.3/baixar_musica_qt.exe').Path)" baixarMusicaYouTube/BaixarVideoYouTubeSetup.iss
```

Feche a versão anterior antes de usar a nova ou instalar a atualização. O build padrão continua usando `dist/baixar_musica_qt.exe`; `AppExecutable` apenas permite selecionar uma saída alternativa para o instalador.

## Android debug

Requisitos: JDK 17; Android SDK com `platforms;android-36` e `build-tools;36.0.0`. Os scripts Windows usam o JDK indicado por JAVA_HOME ou procuram `Program Files/Java/jdk-17`; recusam outra versão. O Gradle pode instalar componentes SDK faltantes quando as licenças já estão aceitas.

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\.venv\Scripts\python.exe scripts/check_android_blur.py
.\.venv\Scripts\python.exe scripts/check_android_sources.py
powershell -ExecutionPolicy Bypass -File baixarMusicaYouTubeAndroid/build_android.ps1
. baixarMusicaYouTubeAndroid/setup_android.ps1
& baixarMusicaYouTubeAndroid/gradlew.bat -p baixarMusicaYouTubeAndroid --no-daemon --console=plain lintDebug
.\.venv\Scripts\python.exe scripts/check_apk.py baixarMusicaYouTubeAndroid/app/build/outputs/apk/debug/app-debug.apk
```

Linux/macOS, com JAVA_HOME e ANDROID_HOME configurados:

```bash
python3 scripts/check_android_blur.py
python3 scripts/check_android_sources.py
cd baixarMusicaYouTubeAndroid
bash build_android.sh
bash gradlew lintDebug
```

Saída: `app/build/outputs/apk/debug/app-debug.apk`. O verificador Python da raiz confere as quatro ABIs, FFmpeg/FFprobe/Python/QuickJS, EJS, catálogo compartilhado e extratores das seis fontes. O APK debug usa assinatura de desenvolvimento e não substitui automaticamente uma instalação release assinada com outra chave. Os scripts Windows direcionam o cache Gradle a `work/gradle`, salvo configuração explícita de `GRADLE_USER_HOME`.

## Verificar as novas fontes

```text
python -m unittest discover -s tests -v
python scripts/validate_media.py
python scripts/validate_posts.py
python scripts/check_android_sources.py
```

O teste de posts usa mídia local gerada pelo comando anterior: seleção do segundo vídeo, todos e preservação de resultados em falha parcial. A política Java de URLs usa os mesmos casos do desktop. GitHub Actions executa essas verificações e os builds, sem publicação automática. Amostras públicas são optativas: `python scripts/validate_sources.py --network`; precisam de rede, transferem recortes de 3 s por padrão e não rodam no CI. Exemplos completos/seleção e limites estão em [SOURCES.md](SOURCES.md).

## Android release e assinatura

`build_android_release.ps1` mantém o fluxo existente: lê `release-signing/keystore.properties` e, na primeira execução sem configuração, cria material local de assinatura. Guarde essa pasta fora do Git; mudar/perder a chave impede atualizar instalações existentes. A compilação debug não valida a assinatura release: confira também o APK release com apksigner e o verificador de recursos.

## Reunir instaladores em outputs

`outputs/` é uma pasta local ignorada pelo Git para os arquivos que o mantenedor poderá anexar a uma release. Código, licenças e ferramentas de empacotamento continuam versionados; os comandos abaixo não publicam releases.

| Plataforma | Arquivo |
| --- | --- |
| Windows x64 | `outputs/UIfor_yt-dlp-v3.3-windows-x64-setup.exe` |
| Android 10+ | `outputs/UIfor_yt-dlp-v3.3-android-release.apk` |
| Linux x86_64 | `outputs/UIfor_yt-dlp-v3.3-linux-x86_64.tar.gz` |

Windows, após compilar/conferir o EXE selecionado:

```powershell
New-Item -ItemType Directory -Path outputs -Force | Out-Null
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' "/DAppExecutable=$((Resolve-Path 'baixarMusicaYouTube/dist/audit/baixar_musica_qt.exe').Path)" "/O$((Resolve-Path 'outputs').Path)" '/FUIfor_yt-dlp-v3.3-windows-x64-setup' baixarMusicaYouTube/BaixarVideoYouTubeSetup.iss
```

`dist/audit` é a saída separada validada na auditoria. Para builds futuros, ajuste AppExecutable para o EXE recém-compilado. O instalador conserva identidade, atalhos e licenças. Sem certificado de assinatura Windows configurado, o setup permanece sem Authenticode.

Android, usando a chave release existente:

```powershell
New-Item -ItemType Directory -Path outputs -Force | Out-Null
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
Push-Location
try {
    & .\baixarMusicaYouTubeAndroid\build_android_release.ps1
} finally {
    Pop-Location
}
Copy-Item baixarMusicaYouTubeAndroid/Output/BaixarMusicaYouTube_Android_v3.3_release.apk outputs/UIfor_yt-dlp-v3.3-android-release.apk
.\.venv\Scripts\python.exe scripts/check_apk.py outputs/UIfor_yt-dlp-v3.3-android-release.apk
```

Verifique também a assinatura com apksigner e a versão com aapt. APK release usa a identidade/chave existente; APK debug tem outra assinatura e não pode ser atualizado diretamente por esse arquivo. Nunca inclua a pasta release-signing no pacote ou no Git.

Linux precisa ser compilado em Linux. Depois do build e de `scripts/check_bundle.py`, a partir da raiz:

```bash
python scripts/package_linux.py
```

O pacote contém o executável, `install_linux.sh`, ícone, README, GPLv3 e avisos/licenças das ferramentas. A instalação é por usuário:

```bash
tar -xzf UIfor_yt-dlp-v3.3-linux-x86_64.tar.gz
cd UIfor_yt-dlp-v3.3-linux-x86_64
bash install_linux.sh
```

O job Linux do GitHub Actions gera e disponibiliza esse `.tar.gz` como artefato separado `Linux-package`, sem publicação automática. É possível baixar esse artefato para `outputs/` quando o host Windows não possui ambiente Linux. O runner é Ubuntu 24.04; bibliotecas do sistema/glibc limitam a compatibilidade e o pacote deve ser testado na distribuição de destino. Não se trata de build ARM64, DEB ou RPM.

Na entrega local, `LEIA-ME.md`, `build-info.json` e `SHA256SUMS.txt` documentam origem, assinatura, validação e hashes. Os hashes devem ser recalculados ao regenerar qualquer instalador. Instalação limpa Windows, atualização Android e execução gráfica Linux continuam verificações distintas dos builds/inspeções.

## Conferência antes de distribuir

1. Reproduzir build a partir de um checkout sem cookies nem dependências globais Python.
2. Executar testes, conversões e verificadores; registrar versões e limitações em `VALIDATION.md` e `DEPENDENCIES.md`.
3. Testar manualmente interface no Windows/DPI, Linux de destino e downloads no Android físico.
4. Acompanhar GPLv3, avisos completos e acesso ao código-fonte correspondente, inclusive dos componentes que o exigem. Conferir origem/configuração do FFmpeg usado.
5. Anexar EXE/instalador/APK/pacote a uma release somente após validação e decisão do mantenedor. GitHub Actions produz artefatos temporários de teste, não releases públicas.

Antes do seu commit, confira `git status --short` e `git ls-files --others --exclude-standard`. Nenhum cookie, arquivo de assinatura, ambiente virtual ou binário deve aparecer. Não é necessário apagar os arquivos locais ignorados.

English: use isolated environments and the commands above. Build Windows on Windows and Linux on Linux. Android uses JDK 17, SDK 36 and the existing application identity/signing flow. Never package cookies or publish signing material. CI artifacts are temporary checks, not automatic public releases. Preserve licenses and corresponding source access when distributing binaries.
