# Baixar Música YouTube Linux · base pública v3

Versão PySide6/yt-dlp mantida nesta pasta. Janela fixa 980 × 760; MP4, MP3, WEBM, MKV, GIF e WAV; YouTube nesta etapa.

A produção atual do app é feita principalmente por IA, com orientação humana. Isso se refere ao nosso código e não às dependências. Leia a história completa e as instruções em [README português](../README.md) ou [English README](../README.en.md).

## Execução e build

Use Python 3.11 ou superior com wheel PySide6 compatível e instale FFmpeg/FFprobe na distribuição. Os requisitos Python são compartilhados com Windows na raiz.

Na raiz:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python scripts/setup_tools.py --system-ffmpeg --output-dir baixarMusicaYouTubeLinux/bin
.venv/bin/python baixarMusicaYouTubeLinux/baixar_musica_qt.py
cd baixarMusicaYouTubeLinux
bash build_linux.sh
```

Deno é preparado pelo bootstrap; FFmpeg/FFprobe são copiados do sistema. O build gera `dist/baixar_musica_qt` e `Output/baixar-musica-youtube-linux-v3.tar.gz`, com ícone, instalador por usuário e licenças.

```bash
bash install_linux.sh
```

Instala em `~/.local/opt/baixar-musica-youtube` e cria atalho sem sudo. PyInstaller exige Linux para produzir um executável Linux. Um pacote compilado em uma distribuição não certifica todas as versões de glibc/sistema.

## Cookies, licença e validação

Sem cookies por padrão. `UIFOR_YTDLP_COOKIES` pode apontar para um arquivo Netscape externo escolhido por você. Cookies jamais são empacotados.

Código GPLv3; dependências mantêm suas licenças. Consulte [Build](../docs/BUILD.md), [Validação](../docs/VALIDATION.md) e [Terceiros](../THIRD_PARTY_NOTICES.md). Esta base não anuncia binários Linux antigos como releases verificadas.
