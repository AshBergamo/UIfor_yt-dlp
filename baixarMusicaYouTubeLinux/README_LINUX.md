# UIfor_yt-dlp Linux · V3.3

Versão PySide6/yt-dlp mantida nesta pasta. Nova interface com temas claro/escuro persistentes, janela redimensionável e maximização normal que preserva os painéis do sistema. MP4, MP3, WEBM, MKV, GIF e WAV; YouTube nesta etapa. Miniatura original quando disponível, com ícone genérico em caso de falha.

A primeira abertura maximiza a janela; as próximas restauram tamanho/estado. Em largura menor, formulário e andamento ficam empilhados. O visual usa superfícies e luz internas; não depende de blur do compositor. O fonte desktop atual é igual ao Windows, mas a execução gráfica desta revisão no Linux ainda está pendente.

A thumbnail carregada também vira fundo com desfoque suave, recorte proporcional e camada azul/perolada para o tema. Painéis translúcidos preservam controles nítidos; rolagem e troca de tema reutilizam a cópia preparada. Editar/apagar o link restaura o gradiente e os painéis opacos, sem erro. O efeito usa Qt já instalado, sem consulta adicional e sem depender do compositor Linux.

A produção atual do app é feita principalmente por IA, com orientação humana. Isso se refere ao nosso código e não às dependências. Leia a história completa e as instruções em [README português](../README.md) ou [English README](../README.en.md).

Fontes integradas: YouTube, Instagram, X/Twitter, Facebook, Twitch e TikTok experimental. Prévia automática e seleção individual/todos em posts com vídeos. Veja [fontes e validação](../docs/SOURCES.md); execução gráfica Linux desta expansão permanece pendente.

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

Deno é preparado pelo bootstrap; FFmpeg/FFprobe são copiados do sistema. O build gera `dist/baixar_musica_qt` e `Output/baixar-musica-youtube-linux-v3.3.tar.gz`, com ícone, instalador por usuário e licenças.

```bash
bash install_linux.sh
```

Instala em `~/.local/opt/baixar-musica-youtube` e cria atalho sem sudo. PyInstaller exige Linux para produzir um executável Linux. Um pacote compilado em uma distribuição não certifica todas as versões de glibc/sistema.

## Cookies, licença e validação

Sem cookies por padrão. `UIFOR_YTDLP_COOKIES` pode apontar para um arquivo Netscape externo escolhido por você. Cookies jamais são empacotados.

Código GPLv3; dependências mantêm suas licenças. Consulte [Build](../docs/BUILD.md), [Validação](../docs/VALIDATION.md) e [Terceiros](../THIRD_PARTY_NOTICES.md). Esta base não anuncia binários Linux antigos como releases verificadas.
