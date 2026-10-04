# Validação / Validation

## Conferência para o commit e push da V3.3 — 2026-10-04

O mantenedor autorizou commit e push da expansão e da numeração V3.3. Os 38 candidatos foram revisados: catálogo/fontes, consultas, interface de seleção, conversão WEBM, versões, documentação/capturas e verificações de build/CI. Python/JSON/YAML, links locais, igualdade dos fontes desktop e `git diff --check` passaram. Os 26 testes e os builds Windows/APK conferidos na seção abaixo correspondem aos fontes desta revisão; as edições posteriores são documentais. Binários, cookies, assinatura, caches e ambientes continuam fora do Git. O resultado do GitHub Actions desta revisão será uma verificação posterior ao push; validação local não antecipa aprovação remota.

As menções anteriores a ausência de commit/push registram o estado de cada etapa antes desta autorização.

## V3.3 e relato do teste no celular — 2026-10-04

O mantenedor informou que o aplicativo funcionou no celular. Esse é um relato de teste manual em aparelho real, referente ao APK da expansão entregue antes da mudança do número de versão; não foram detalhados modelo, versão Android, sites, formatos, rotação ou medições. Ele substitui a pendência geral de obter um primeiro teste físico, preservando a necessidade de cobertura por dispositivo/fonte/formato. Os registros anteriores abaixo descrevem o que havia sido comprovado em cada etapa.

O número exibido no rodapé/Sobre passa a **V3.3** nos três aplicativos. Qt declara versão 3.3, Android usa versionName 3.3/versionCode 4, e o instalador Windows declara 3.3.0. A primeira base pública continua sendo v3 na história do projeto. README principal explica novidades, funções, formatos, fontes, uso, plataformas, IA e limites; inglês e descrições específicas acompanham essa informação. Esta revisão altera numeração/documentação, preservando o comportamento de download já testado. Linux gráfico/build atual, Twitch VOD, TikTok e CI remoto continuam com os limites descritos abaixo.

Conferência desta mudança: os 26 testes passaram; fontes desktop idênticos, sintaxe Python/PowerShell/Bash, JSON/YAML, links locais e `git diff --check` aprovados. Novo EXE em `baixarMusicaYouTube/dist/v3.3/baixar_musica_qt.exe`: build limpo, recursos/licenças/ausência de cookies conferidos, janela aberta e fechada com código 0. APK debug recompilado e conferido; aapt confirmou versionName 3.3/versionCode 4, identidade preservada, quatro ABIs e ferramentas/EJS. Android lint: 0 erros e 22 avisos. Logs em `work/tests-v33.log` e `work/build-v33-*.log`. Scripts/nomes de distribuição foram atualizados; instalador Windows, pacote Linux e APK release não foram gerados nesta mudança. Sem commit/push/publicação.

English: the maintainer reported successful phone use of the previously delivered expansion APK; no detailed test matrix was supplied. The app label is now V3.3 across platforms, without changing download behavior. Historical validation below retains the evidence available at each stage.

## Expansão de fontes — 2026-10-04

Instagram, X/Twitter, Facebook, Twitch e TikTok foram integrados aos três aplicativos, preservando YouTube, seis formatos, playlists existentes, temas, fundo/capas e identidade Android. TikTok permanece **experimental**. A tabela registra resultados desta revisão; as seções anteriores preservam o histórico de cada etapa.

| Verificação | Resultado e limite |
| --- | --- |
| Regressões desktop | 26 testes passaram. Os dois fontes desktop continuam idênticos. Cobertura inclui 41 casos de links, redirecionamentos limitados, índices com lacunas, seleção/limpeza de post, erro silencioso de prévia, espera de escolha depois de descoberta explícita, falha parcial e ausência de fallback YouTube para HTTP 403 de outros sites. |
| Conversões e capas | Seis formatos e uma rota adicional H.264/AAC → WEBM passaram com mídia local/FFprobe; WEBM convertido tem VP9/Opus. Seis casos de capa JPEG/WebP/ausente em MP4/MKV passaram, preservando hashes dos streams de áudio/vídeo e sem imagem separada. |
| Posts locais | Transferências reais pelo servidor HTTP local: segundo item gerou um arquivo, todos geraram três; item intermediário indisponível gerou erro parcial e preservou dois. Títulos iguais produziram nomes diferentes por ID/índice. O HTTP 404 neste teste é intencional. |
| YouTube | Recorte público sem cookies de `jNQXAC9IVRw`: MP4 de 3,014 s, vídeo/áudio e capa. Os testes locais também preservam playlists e limite GIF de 30 s. |
| Instagram | Reel `Chunk8-jurw` completo: 4,966667 s, 2.159.577 bytes, capa. Post `BQ0eAlwhDrw`: três vídeos completos de 4,004004 / 6,506507 / 31,698365 s, todos com capa. Seleção do segundo item gerou somente seu MP4 de 31,698365 s. |
| X/Twitter | Status `719944021058060289` completo: 3,178667 s, 620.539 bytes, capa. |
| Facebook | Reel `1591316522498163` completo: 21,833333 s, 10.063.774 bytes, capa. Outra amostra antiga falhou na extração; não se promete funcionamento de todos os links. |
| Twitch | Clip `FaintLightGullWholeWheat` completo: 32,099 s, 16.478.488 bytes, capa. VOD ainda sem amostra real. |
| TikTok | As duas amostras consultadas falharam com `Unexpected response from webpage request`. Integração aceita o link e apresenta erro legível ao baixar; sucesso de download não comprovado. |
| Interface Windows | Qt nativo: prévia automática do post Instagram encontrou três vídeos; escolha do segundo, temas claro/escuro, janela compacta e botão Baixar passaram. Download final de 31,698365 s com capa confirmado por FFprobe. Capturas reais em `docs/images/ui-fontes-*.png`. |
| EXE Windows | Build limpo em `baixarMusicaYouTube/dist/fontes/baixar_musica_qt.exe`. Conferidos catálogo, módulos de consulta/extratores, ferramentas, EJS, QtNetwork/TLS/licenças e ausência de cookies. Consulta real no EXE sem console encontrou os três vídeos por IPC local. Smoke abriu UIfor_yt-dlp e fechou com código 0; neste smoke restaurou preferência de janela não maximizada. |
| Android host/pacote | Política Java passou os mesmos 41 casos, erros legíveis e filtro de publicação apenas do formato final escolhido. Filtro CPU do fundo passou. assembleDebug/lintDebug passou: 0 erros, 22 avisos não ocultados. APK conferido: quatro ABIs, catálogo, extratores, ferramentas, QuickJS/EJS/licenças e ausência de cookies/material de assinatura. |
| Limites | Amostras públicas e execução gráfica realizadas no Windows, com yt-dlp 2026.08.19 e FFmpeg/FFprobe 9.0.2, sem cookies pessoais. Não certificam todos os links, regiões, codecs ou conteúdos sem áudio. Android físico, Linux gráfico/build atual, Twitch VOD e instalação limpa continuam pendentes. Android empacota backend 2025.11.12 e tenta atualizar antes do primeiro uso. |
| GitHub Actions e entrega | CI inclui regressões, conversões/posts locais, política Java, builds e inspeção de recursos. Os testes públicos são optativos, fora do CI. A revisão ainda não rodou no GitHub; nenhum commit, push, instalador novo, release ou publicação de binários foi feito nesta etapa. |

Uma falha inicial no verificador Facebook veio do FFprobe decodificado como cp1252: um título Unicode expôs o erro. O harness passou a ler UTF-8; a aplicação não precisou de alteração por esse diagnóstico. O APK usa `youtube/__init__.py`, e o verificador passou a reconhecer esse pacote, evitando confundi-lo com um extrator ausente. A espera do teste gráfico usa o laço normal de eventos Qt e monitor na thread principal; esperar o worker apenas por chamadas repetidas de QTest bloqueou o harness. Somente os processos desse teste foram encerrados. Em um MP4 Instagram, o incorporador mutagen falhou e o fallback oficial FFmpeg gravou a capa corretamente; nenhuma dependência foi editada.

Reprodução e escopo: [Fontes](SOURCES.md), [Build](BUILD.md). Relatórios/mídia públicos sanitizados em `work/validation/public-sources/` e resultado gráfico em `work/native-source-ui/result.json`, ambos locais e ignorados pelo Git.

English: six sources are integrated, with silent cancellable previews and individual/all selection for multi-video posts. Twenty-six desktop tests, shared Java URL cases, six formats plus H.264/AAC-to-WebM, cover tests, local post transfers, native Windows UI and Windows/Android packaging passed. Complete Windows samples passed for Instagram, X, Facebook and Twitch; TikTok stays experimental after extraction failures. Physical Android, current Linux runtime/build, Twitch VOD, clean installation and hosted CI remain pending. No commit/push or release was made in this stage.

## Conferência para o commit autorizado — 2026-10-04

O mantenedor autorizou o registro local desta revisão, reunindo nova UI, prévia automática, fundo com thumbnail e capas MP4/MKV. Antes do commit, os quinze testes desktop foram repetidos com sucesso, assim como as seis conversões locais e os testes de capas JPEG/WebP/ausente, preservando os streams de vídeo/áudio. O filtro CPU Android, `pip check`, conferência de recursos do EXE/APK, igualdade dos fontes desktop, links/JSON da documentação e `git diff --check` também passaram. Cookies, binários, caches e material de assinatura ficaram fora dos candidatos ao commit.

Os resultados gráficos e builds locais abaixo pertencem à mesma revisão de código; não foram refeitos builds sem mudança do fonte. Android físico, Linux gráfico, instalação limpa e CI após push continuam pendentes. Os registros anteriores de “sem commit/push pelo agente” descrevem cada etapa antes desta autorização. A publicação no GitHub será uma ação separada.

## Fundo com a thumbnail — 2026-10-04

| Verificação | Resultado e limite |
| --- | --- |
| Desktop atual | Quinze testes passaram nos dois fontes: nova cobertura do desfoque/cache, original preservado, bordas, recorte vertical/horizontal, falha opcional, limpeza, respostas antigas e transição para download. Tema/resize/rolagem não reprocessam a foto. |
| Contraste | Imagens preta/branca extremas exercitadas nos dois temas. Legendas pequenas fora dos painéis usam branco/texto escuro com imagem ativa; legendas e textos/erros dos painéis passaram o limite de 4,5:1. Isso não é auditoria completa de acessibilidade do aplicativo. |
| Capturas nativas | Dois vídeos públicos forneceram thumbnail e fundo antes de Baixar, sem cookies: `qGGkQORaVzY` e `jNQXAC9IVRw`. ID inexistente preservou gradiente/painéis opacos, sem erro. Progresso em 0%, botão habilitado, nenhum worker. Temas em `docs/images/ui-fundo-*.png`, capturas reais Windows. |
| Escala e rolagem | Qt Windows em 100/125/150/200%, maximização normal e janela compacta; barras do sistema preservadas, sem rolagem horizontal. Fixture vertical conservou cache 360 × 640 e fundo fixo na rolagem. Limita-se a este monitor, não a todos os DPIs/compositores. |
| Download público | MP4 de `jNQXAC9IVRw` pela janela Qt, sem cookies: fundo preservado antes/ao iniciar/depois de concluir e tema alterado durante trabalho. FFprobe: 19,014 s, vídeo/áudio e attached_pic; uma capa JPEG em covr. Backend/conversões não foram alterados nesta etapa. |
| Windows | Build limpo em `baixarMusicaYouTube/dist/fundo/baixar_musica_qt.exe`; check_bundle aprovou ferramentas/EJS/QtNetwork/TLS/licenças e ausência de cookies. Smoke do EXE abriu UIfor_yt-dlp maximizado e fechou com código 0. Inno gerou `Output/BaixarMusicaYouTube_Setup_v3.exe` com esse EXE. Instalação limpa pendente. Versões anteriores preservadas. |
| Android CPU | `scripts/check_android_blur.py` passou com JDK 17. Filtro comparado com convolução de referência, incluindo dimensões 1 px, alpha, bordas, cores sólidas, raio zero, entradas inválidas e original intacto. Cache máximo 640 × 640 levou cerca de 54 ms neste PC; não representa desempenho de celular. |
| Android pacote | assembleDebug/lintDebug passou, 0 erros e 20 avisos não ocultados. APK conferido: quatro ABIs, ferramentas, EJS/licenças, classes novas do fundo e ausência de cookies/material de assinatura. Assinatura debug; não instalado nem publicado. |
| Limites | UI/teclado/rotação/rolagem e download no Android físico, execução gráfica/build Linux desta revisão e GitHub Actions depois do commit/push continuam pendentes. A etapa não acrescenta suporte a outros sites. |

O filtro Qt arredondou a opacidade em algumas bordas opacas; a cópia de imagens sem alpha volta ao formato RGB32 após o desfoque, preservando opacidade. A primeira captura imediata após trocar tema mostrou uma pintura parcial da miniatura; aguardar os eventos de pintura no harness corrigiu a captura, sem mudar o original ou o pipeline. Testes de contraste motivaram apenas o ajuste de cor das legendas externas. O cache só é preparado ao chegar uma nova foto; nenhum timer de animação contínua foi adicionado.

Reprodução adicional: `python scripts/check_android_blur.py` (JDK via JAVA_HOME). Testes desktop e comandos dos builds estão em [BUILD.md](BUILD.md). Windows validado visualmente; APK compilado não comprova renderização em aparelho. Não houve commit/push/publicação pelo agente.

English: cached thumbnail backgrounds are implemented across the three sources, with theme overlays, translucent panels, sharp controls and silent fallback. Fifteen desktop regressions, native Windows captures/DPI checks, a public download, Windows packaging and Android CPU/build/lint checks passed. Physical Android, current Linux graphical/build and hosted CI validation remain pending.

## Nova interface — 2026-10-04

Implementação autorizada após os conceitos e a escolha dos dois temas. O suporte continua sendo YouTube; esta revisão não adiciona outros sites.

| Verificação | Resultado e limite |
| --- | --- |
| Regressões desktop atuais | Nove testes passaram, exercitando Windows e Linux pelo Qt deste host Windows: formatos/erro, URLs/playlist, GIF, cookies, ferramentas, tema preservando campos/operação, maximização/restauração, thumbnail opcional e metadados/conversão indeterminada. Não certificam o gerenciador de janelas Linux. |
| Miniatura | HTTP local confirmou pixels da imagem original, persistência ao trocar tema, fallback em 404/imagem acima do limite e preservação do progresso. Protocolo não aceito não inicia requisição. |
| Download público pela nova UI | Botão da janela Qt acionado pelo script local: `jNQXAC9IVRw` baixou MP4 sem cookies, mostrou título/thumbnail originais e passou por troca de tema durante a operação. FFprobe: 19,014 s, streams de vídeo e áudio. |
| Conversões reais | Repetidos MP4, MP3, WEBM, MKV, GIF e WAV com mídia local e FFprobe; todos passaram. Medições permanecem na tabela abaixo. |
| Capturas Windows | Backend Qt nativo, 192 famílias de fontes; temas claro/escuro e janela compacta/GIF conferidos. Capturas em `docs/images/ui-desktop-*.png` mostram a área interna do app. Não são os mockups gerados por IA. |
| Janela e escala | Maximização normal, restauração e layouts estreitos exercitados. Escalas Qt 1/1,25/1,5/2 neste monitor 1920 × 1080; janela maximizada respeitou o limite inferior da área útil em todas. Em 200%, mínimo foi limitado a 720 × 476 unidades lógicas. Isso não certifica todos os monitores, configurações de DPI ou leitores de tela. |
| Windows empacotado | Executável PyInstaller atualizado, aberto e fechado normalmente pelo smoke. QtNetwork e backends TLS, ferramentas/EJS/licenças conferidos; sem recurso de cookies. |
| Instalador | Setup Inno atualizado com nome/ícone UIfor_yt-dlp e identidade/caminho de instalação existentes. Build conferido; instalação limpa continua pendente. |
| Android | APK debug da nova UI compilado e inspecionado: quatro ABIs, ferramentas, QuickJS/EJS e licenças presentes. Lint: 0 erros, 19 avisos de SDK/versões, configuração de recursos, ícone monocromático e textos/tradução; não ocultados. |
| Android e Linux gráficos | Sem dispositivo conectado nem AVD configurado; sem sessão Linux disponível. Tema, thumbnail, teclado, rotação e downloads Android precisam de teste em aparelho. Conferência gráfica e build desta revisão Linux dependem do ambiente Linux/CI. |
| GitHub Actions | Nenhuma execução remota desta revisão antes do commit/push do mantenedor. Resultados da base antiga abaixo não comprovam esta nova UI. Não houve commit, push ou publicação pelo agente. |

Problemas locais resolvidos: o daemon Gradle criado no sandbox manteve a restrição de leitura dos JARs; reiniciá-lo com acesso adequado e `--no-daemon` permitiu compilar. O empacotamento incremental Android falhou uma vez e passou na repetição, sem diagnóstico conclusivo dessa falha transitória. O primeiro script de smoke da UI agendou a finalização na thread do worker; o download terminou, mas a janela de teste ficou aberta. O script passou a acompanhar a finalização por temporizador na thread principal, e o teste completo passou. Somente os processos dos testes criados nesta tarefa foram encerrados.

O primeiro pacote Windows falhou ao importar QtCore: a análise coletou `icuuc.dll` do Poppler e `ucrtbase.dll` de outra ferramenta disponível no PATH. A comparação de exports confirmou funções ICU exigidas pelo Qt ausentes na DLL do Poppler e presentes na DLL do Windows. O helper de build agora isola a busca Windows ao Python/ambiente do projeto e ao sistema, após resolver as ferramentas. Um build limpo excluiu essas DLLs alheias; o executável abriu com título UIfor_yt-dlp, maximizado, e fechou com código 0. Um processo do teste anterior precisou ser encerrado para liberar o EXE antes da substituição. Não basta verificar que o processo permaneceu ativo: o smoke agora confirma a janela do próprio executável.

English: the new native UI is implemented in all three apps. Desktop regressions, six local conversions, a public download with original thumbnail and a theme switch during the operation passed on Windows. Windows packaging and Android debug build/lint passed. Linux graphical and physical Android validation remain pending; the current revision has not run in hosted CI.

## Prévia automática antes do download — 2026-10-04

- Desktop Windows/Linux e Android buscam título/thumbnail pelo oEmbed público do YouTube, após pausa de 450 ms em um link de vídeo completo. Não iniciam download, extração de formatos, Deno/FFmpeg ou atualização do backend. Sem chave e sem cookies pessoais; playlists sem ID de vídeo e mídia privada/restrita podem não ter prévia.
- Consulta assíncrona, tamanho máximo de JSON 128 KiB e tempos limitados. Trocar/apagar o link, iniciar download ou fechar descarta a consulta anterior. Não há mensagem de erro de prévia nem bloqueio do botão Baixar. A prévia mantém progresso em 0%; o download continua buscando metadados próprios. O título/imagem disponíveis são preservados na transição.
- Onze testes desktop passaram, exercitando ambos os fontes. Novos testes cobrem normalização de watch/short link/Shorts/live/embed, link incompleto/domínio falso/lista sem vídeo, debounce, título UTF-8 e imagem reais via HTTP local, resposta atrasada de link antigo, JSON inválido, HTTP 404, limite de bytes e cancelamento ao começar download. Tema/campos, worker, formatos e capas anteriores preservados.
- Teste Qt nativo Windows, sem clicar Baixar e sem destino selecionado: o link da imagem fornecida (`qGGkQORaVzY`) exibiu título/thumbnail originais em 1,20 s; o vídeo público `jNQXAC9IVRw` em 0,78 s. Um ID inexistente manteve o espaço reservado, sem erro. Todos conservaram 0%, botão habilitado e nenhum worker de download. São medições desta conexão, não garantia de latência. Captura real em `docs/images/ui-previa-escuro.png`; temas claro/escuro conferidos.
- Android debug/build/lint passou: APK inspecionado, quatro ABIs/ferramentas/EJS/licenças e código da consulta presentes; 0 erros, 20 avisos. UI/consulta/download em aparelho ainda pendentes. Linux gráfico/novo build e CI remoto desta revisão pendentes.
- Download público também passou ao clicar Baixar antes da consulta terminar e depois de a prévia estar carregada: título/imagem preservados na transição, troca de tema em andamento e capa JPEG incorporada no MP4 de 19,014 s. Nenhum cookie pessoal usado.
- Novo EXE em `baixarMusicaYouTube/dist/previa/baixar_musica_qt.exe`, arquivo conferido e janela nativa maximizada aberta/fechada com código 0. Instalador em `baixarMusicaYouTube/Output/BaixarMusicaYouTube_Setup_v3.exe` gerado com esse EXE. As versões anteriores em `dist/` e `dist/capa/` não foram substituídas nem seus processos encerrados.
- O fundo com thumbnail translúcida solicitado foi explicitamente adiado pelo usuário: esta etapa implementa só a prévia. Não houve commit/push/publicação; alterações de UI/capas anteriores preservadas.

English: automatic title/thumbnail preview passed in the native Windows UI before any download, including the user-provided public video link and a silent unavailable-video case. Eleven desktop tests cover debounce, stale responses, limits and download cancellation. Android debug build/lint passed, but physical Android, current Linux and hosted CI checks remain pending. The thumbnail background is deferred.

## Thumbnail incorporada como capa — 2026-10-04

- Windows/Linux: MP4 (incluindo as rotas alternativas) e MKV usam `writethumbnail`, conversão JPEG antes do download e `EmbedThumbnail` depois do merge/remux. A imagem temporária é removida. Android usa as opções equivalentes do yt-dlp e só publica os seis formatos finais, excluindo imagens temporárias. Bibliotecas externas não foram modificadas.
- Nove regressões desktop passaram. `scripts/validate_media.py` agora também verifica capas JPEG/WebP em MP4/MKV, thumbnail HTTP 404 e ausência de imagem. Todos passaram: capa JPEG incorporada quando disponível, vídeo/áudio com os mesmos hashes de pacotes da fonte, duração preservada e nenhuma imagem separada na saída. O teste faz parte do comando já usado pelo CI.
- Comparação pelo `IShellItemImageFactory` nativo do Windows: MP4 sem capa mostrou um quadro de teste; com capa incorporada por mutagen ou FFmpeg mostrou a imagem vermelha de referência. O MP4 produzido pelo pipeline atual também mostrou essa capa. O MKV tinha a capa verificada por FFprobe, mas o handler deste Windows continuou exibindo o quadro do vídeo. Não prometer a mesma prévia em todo formato/player/sistema; [API oficial de miniaturas do Windows](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ishellitemimagefactory-getimage).
- Download público curto pela UI, sem cookies, passou novamente: `jNQXAC9IVRw`, 19,014 s, vídeo AV1 + áudio Opus + capa JPEG. A imagem `covr` extraída do MP4 correspondeu à miniatura exibida pelo Shell do Windows. Troca de tema e thumbnail da UI também passaram.
- EXE em `baixarMusicaYouTube/dist/capa/baixar_musica_qt.exe`: módulos de capa/mutagen, ferramentas, QtNetwork/TLS/EJS/licenças conferidos; sem cookies. Smoke abriu a janela UIfor_yt-dlp maximizada e fechou com código 0. Instalador atualizado gerado a partir desse EXE via `AppExecutable`. O EXE anterior estava aberto pelo usuário e foi preservado; nenhum processo do usuário foi encerrado.
- Android debug/build/lint passou; APK conferido, quatro ABIs, 0 erros e 19 avisos. Ainda falta download e exibição em aparelho. Linux gráfico/build desta revisão e CI remoto continuam pendentes. Não houve commit/push/publicação. Downloads antigos não são alterados automaticamente; WEBM/GIF e formatos de áudio continuam com o comportamento anterior.

English: MP4/MKV now embed the original thumbnail. Local JPEG/WebP and missing-thumbnail checks preserved encoded video/audio and left no sidecar images. Windows showed MP4 artwork through its native Shell API; its MKV handler continued showing a video frame despite the embedded cover. A public cookie-free download, Windows EXE/installer and Android debug build/lint passed. Physical Android and current Linux/hosted CI validation remain pending.

## Preparação da base v3 — 2026-10-04

| Verificação | Resultado e limite |
| --- | --- |
| Ambiente Python limpo | Python 3.11.9, dependências aprovadas instaladas e `pip check` sem conflitos. |
| Regressões desktop | Cinco testes passaram, cada um exercitando as duas implementações: URLs/playlist, limites GIF, cookies explícitos, descoberta de ferramentas e restauração da UI após erro. |
| Conversões reais locais | MP4, MP3, WEBM, MKV, GIF e WAV passaram com mídia sintética servida por HTTP local e inspeção FFprobe. Isso verifica o pipeline de conversão, não a extração de todos os sites. |
| Download YouTube | Vídeo público curto `jNQXAC9IVRw` baixado pelo pipeline MP4 sem cookies pessoais. Teste pelo engine, não por automação de clique na UI. |
| Janela Windows | Aberta com backend Qt Windows e captura da própria janela conferida; interface atual e aviso GPLv3/IA preservados. Não houve certificação em todos os DPIs. |
| Executável Windows | PyInstaller 6.22.3 gerou o arquivo; arquivo interno conferido com FFmpeg/FFprobe/Deno/EJS/licenças e sem recurso de cookies. Permaneceu ativo durante smoke de 12 segundos. |
| Instalador Windows | Inno Setup 6.6.1 compilou o setup v3 com licenças. Instalação limpa do setup não foi executada. |
| APK debug Android | Build com AGP 9.4.0/Gradle 9.6.0/JDK 17 passou após atualização transitiva; quatro ABIs e recursos/licenças conferidos. |
| Android lint | 0 erros, 18 avisos; avisos de SDK/versões mais novas, recursos e textos/tradução. Não foram ocultados. |
| Android EJS/QuickJS | APK inclui scripts EJS. Bytecode do wrapper confirma configuração automática de QuickJS. Backend yt-dlp embutido é 2025.11.12; atualização em runtime existente usa canal estável. Execução no celular permanece pendente. |
| Linux | Testes, conversões e empacotamento passaram no runner Ubuntu 24.04 do GitHub Actions. A abertura gráfica do binário Linux permanece pendente. Não foi gerado nem executado um binário Linux neste host Windows; WSL não apresentou distro instalada. |
| GitHub Actions | Primeira execução do commit `b6bc4f6`: Windows e Linux passaram; Android falhou no passo SDK/build com código 127. A localização explícita do sdkmanager foi ajustada e precisa ser validada em uma nova execução. |
| Arquivos para o Git | Cookies, binários, caches, dependências locais e assinatura fora da lista de candidatos. Arquivos locais ignorados preservados; nenhum commit/push feito. |

## Medições locais

| Formato | Duração medida | Streams |
| --- | --- | --- |
| MP4 | 6.0 s | audio, video |
| MP3 | 6.0 s | audio |
| WEBM | 6.008 s | audio, video |
| MKV | 6.023 s | audio, video |
| GIF | 2.14 s | video |
| WAV | 6.0 s | audio |

A fonte sintética tem seis segundos. O GIF solicitado entre 1 e 3 segundos produziu 2,14 segundos; o teste permite 0,2 segundo de tolerância de frames/timestamps. A validação de entrada mantém o limite de 30 segundos; não prometemos cortes com duração exata em toda fonte.

## Problemas encontrados e resolvidos

### Primeira execução no GitHub — 2026-10-04

No [workflow da base pública](https://github.com/AshBergamo/UIfor_yt-dlp/actions/runs/37207167389), Windows e Linux concluíram os testes, conversões, builds e conferência de recursos. O Android interrompeu o passo SDK/build com código 127, antes dos passos de inspeção do APK. As anotações públicas não identificam o comando que faltou; o log completo exige login no GitHub.

O workflow agora localiza o `sdkmanager` diretamente no Android SDK, incluindo pastas versionadas de Command-Line Tools, sem depender de sua presença no PATH. A estrutura segue a [documentação do Android SDK](https://developer.android.com/tools/sdkmanager). Preparação do SDK e build têm passos separados para facilitar o diagnóstico. YAML e sintaxe Bash conferidos localmente; a resolução do erro no runner precisa ser confirmada após commit/push.

### Preparação local

- O bootstrap precisou usar `LICENSE.md` do Deno, em vez de `LICENSE`.
- A fonte MP4 de teste com metadados ao final não funcionou para seek no servidor HTTP simples; gerar a fixture com `+faststart` resolveu. Isso foi uma correção da fixture, não uma mudança da estratégia GIF do app.
- O vídeo de teste antigo `BaW_jenozKc` estava indisponível; o teste público foi repetido com a fonte curta acima.
- AGP 9 rejeitou um Provider diretamente no SourceSet; a pasta de assets gerados foi resolvida como File com dependência explícita do preBuild.
- O backend offscreen Windows não enumerou fontes e produziu quadrados no lugar do texto. A captura válida foi feita com o backend Windows (194 famílias enumeradas); não usamos a captura offscreen como evidência visual.
- O sandbox não conseguiu encerrar a árvore do processo no primeiro smoke; os processos específicos do executável de teste foram encerrados com acesso adequado. Nenhum processo de outro aplicativo foi encerrado.

## Reproduzir

```text
python -m pip check
python -m unittest discover -s tests -v
python scripts/validate_media.py
python scripts/validate_media.py --youtube
python scripts/check_bundle.py
python scripts/check_windows_ui.py  # Windows desktop session only
python scripts/check_apk.py baixarMusicaYouTubeAndroid/app/build/outputs/apk/debug/app-debug.apk
```

Builds e preparação de ferramentas estão em [BUILD.md](BUILD.md); versões resolvidas em [DEPENDENCIES.md](DEPENDENCIES.md). Os relatórios e mídias de teste ficam em `work/` local, ignorado pelo Git.

English: local desktop regressions, six real conversions, one public cookie-free YouTube download, Windows packaging and Android debug build/lint passed. The Windows native Qt window was checked. GitHub-hosted Windows and Linux checks passed, including packaging; Android CI failed with exit code 127. The workflow now locates sdkmanager explicitly and separates SDK preparation from the build, but the fix needs a new hosted run. Linux graphical execution, clean installer installation, all DPI settings and physical Android downloads remain pending. Compilation is not device validation or a full security audit.
