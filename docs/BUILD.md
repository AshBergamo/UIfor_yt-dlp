# Build e distribuição / Build and distribution

Execute os comandos a partir da raiz, salvo indicação contrária. A primeira instalação precisa de internet. Os builds não publicam releases e não criam commits.

## Desktop Windows

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/setup_tools.py --output-dir baixarMusicaYouTube/bin
powershell -ExecutionPolicy Bypass -File baixarMusicaYouTube/build_windows.ps1
.\.venv\Scripts\python.exe scripts/check_bundle.py
```

Saída: `baixarMusicaYouTube/dist/baixar_musica_qt.exe`. Os specs incluem somente ícones, ferramentas, EJS e licenças; **nunca cookies**. Qt usa os hooks do PyInstaller para coletar módulos necessários, sem copiar toda a árvore QML.

Para gerar o instalador, após conferir o executável, use Inno Setup 6:

```powershell
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' baixarMusicaYouTube/BaixarVideoYouTubeSetup.iss
```

Saída: `baixarMusicaYouTube/Output/BaixarMusicaYouTube_Setup_v3.exe`. O instalador acompanha a GPLv3 e os avisos das ferramentas. Binários locais antigos não são evidência de funcionamento do novo fonte.

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

## Android debug

Requisitos: JDK 17; Android SDK com `platforms;android-36` e `build-tools;36.0.0`. Os scripts Windows usam o JDK indicado por JAVA_HOME ou procuram `Program Files/Java/jdk-17`; recusam outra versão. O Gradle pode instalar componentes SDK faltantes quando as licenças já estão aceitas.

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
powershell -ExecutionPolicy Bypass -File baixarMusicaYouTubeAndroid/build_android.ps1
.\.venv\Scripts\python.exe scripts/check_apk.py baixarMusicaYouTubeAndroid/app/build/outputs/apk/debug/app-debug.apk
```

Linux/macOS, com JAVA_HOME e ANDROID_HOME configurados:

```bash
cd baixarMusicaYouTubeAndroid
bash build_android.sh
bash gradlew lintDebug
```

Saída: `app/build/outputs/apk/debug/app-debug.apk`. O verificador Python da raiz confere as quatro ABIs, FFmpeg/FFprobe/Python/QuickJS e EJS. O APK debug usa assinatura de desenvolvimento e não substitui automaticamente uma instalação release assinada com outra chave.

## Android release e assinatura

`build_android_release.ps1` mantém o fluxo existente: lê `release-signing/keystore.properties` e, na primeira execução sem configuração, cria material local de assinatura. Guarde essa pasta fora do Git; mudar/perder a chave impede atualizar instalações existentes. Esta preparação valida APK debug e não executa o script de release nem troca a assinatura do app.

## Conferência antes de distribuir

1. Reproduzir build a partir de um checkout sem cookies nem dependências globais Python.
2. Executar testes, conversões e verificadores; registrar versões e limitações em `VALIDATION.md` e `DEPENDENCIES.md`.
3. Testar manualmente interface no Windows/DPI, Linux de destino e downloads no Android físico.
4. Acompanhar GPLv3, avisos completos e acesso ao código-fonte correspondente, inclusive dos componentes que o exigem. Conferir origem/configuração do FFmpeg usado.
5. Anexar EXE/instalador/APK/pacote a uma release somente após validação e decisão do mantenedor. GitHub Actions produz artefatos temporários de teste, não releases públicas.

Antes do seu commit, confira `git status --short` e `git ls-files --others --exclude-standard`. Nenhum cookie, arquivo de assinatura, ambiente virtual ou binário deve aparecer. Não é necessário apagar os arquivos locais ignorados.

English: use isolated environments and the commands above. Build Windows on Windows and Linux on Linux. Android uses JDK 17, SDK 36 and the existing application identity/signing flow. Never package cookies or publish signing material. CI artifacts are temporary checks, not automatic public releases. Preserve licenses and corresponding source access when distributing binaries.
