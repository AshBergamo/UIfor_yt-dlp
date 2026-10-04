# Componentes de terceiros / Third-party notices

O código da interface e integração do UIfor_yt-dlp usa GNU GPLv3. Cada componente abaixo conserva sua licença, autoria e avisos. A declaração sobre produção por IA refere-se somente ao nosso aplicativo; não descreve o processo de produção dessas dependências.

| Componente | Uso | Licença / fonte |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extração e download | [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE); distribuição PyPI. |
| [yt-dlp-ejs](https://github.com/yt-dlp/ejs) | Solução de desafios JavaScript YouTube | Unlicense, com componentes MIT/ISC; preservar avisos da distribuição. |
| [PySide6 / Qt](https://doc.qt.io/qtforpython-6/licenses.html) | Interface desktop | LGPLv3/GPLv3 ou licença comercial; esta distribuição usa os pacotes de código aberto. Qt inclui componentes com licenças próprias. |
| [FFmpeg / FFprobe](https://ffmpeg.org/legal.html) | Merge, conversão e inspeção | LGPLv2.1+ ou GPL, conforme configuração. Os builds Windows essentials de [Gyan](https://www.gyan.dev/ffmpeg/builds/) habilitam componentes GPL. No Linux, consultar o pacote da distribuição. |
| [Deno](https://github.com/denoland/deno) | Runtime JavaScript desktop | MIT e licenças de componentes internos; fonte e versão registradas em `bin/licenses/`. |
| [youtubedl-android](https://github.com/JunkFood02/youtubedl-android) | Backend Android | GPLv3; inclui Python, FFmpeg e QuickJS, com suas próprias licenças. |
| [Python](https://www.python.org/psf/license/) | Runtime | PSF License; componentes mantêm seus avisos. |
| [QuickJS](https://bellard.org/quickjs/) | Runtime JavaScript Android | MIT. |
| [Jackson](https://github.com/FasterXML/jackson), [Apache Commons](https://commons.apache.org/), [AndroidX](https://developer.android.com/jetpack/androidx) | Dependências transitivas Android | Apache-2.0; preservar os avisos das versões resolvidas. |
| [Kotlin](https://github.com/JetBrains/kotlin) | Runtime utilizado pelo wrapper Android | Apache-2.0. |
| [mutagen](https://github.com/quodlibet/mutagen) | Dependência dos extras yt-dlp | GPLv2+. |
| [requests](https://requests.readthedocs.io/) / [urllib3](https://github.com/urllib3/urllib3) | Rede | Apache-2.0 / MIT. |
| [certifi](https://github.com/certifi/python-certifi) | Certificados | MPL-2.0. |
| [websockets](https://github.com/python-websockets/websockets) | Transporte opcional | BSD-3-Clause. |
| [Brotli](https://github.com/google/brotli) | Descompressão | MIT. |
| [PyCryptodome](https://github.com/Legrandin/pycryptodome) | Criptografia opcional | BSD/public domain, conforme componente. |
| [PyInstaller](https://pyinstaller.org/en/stable/license.html) | Empacotamento | GPLv2+ com exceção para os executáveis gerados; ferramenta de build. |

Este resumo não substitui os textos completos dos pacotes resolvidos. O empacotamento desktop coleta os arquivos de licença presentes nas distribuições Python instaladas, além da GPLv3 do app e dos avisos das ferramentas. A lista de versões resolvidas está em `docs/DEPENDENCIES.md`.

Para distribuir binários, acompanhar a GPLv3, os avisos completos e acesso ao código-fonte correspondente do app e dos componentes que o exigem. Identificar o build FFmpeg, sua configuração e a origem do código correspondente; o instalador de ferramentas registra origem, versão e SHA256. Não atribuir uma mesma licença a todos os componentes nem remover seus créditos. Ver também `docs/BUILD.md`.

Application code is GPLv3. Dependencies retain their own licenses and authorship. The AI disclosure applies only to this application's production. Binary distributions must preserve complete notices and provide corresponding source access where required; this summary does not replace upstream license texts.
