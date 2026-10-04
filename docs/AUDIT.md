# Auditoria e limpeza — 2026-10-04

## Resultado e referência

Todo o código próprio ativo foi inspecionado: desktop Windows/Linux, módulos compartilhados, Android, testes, scripts, estilos embutidos, recursos e configurações de execução/empacotamento. As oportunidades comprovadas foram tratadas em lotes. Nenhuma dependência, formato, fonte suportada ou contrato público foi removido.

Referência inicial: `main`, commit `6bd1c9197663dea9d9a18d55c418654d04bb9c55`, árvore Git e índice limpos; 101 arquivos versionados. Uma cópia desses arquivos foi salva fora da aplicação antes de editar. Não houve commit, stage, push, instalação, release, publicação ou consulta/download em sites externos nesta auditoria. Builds e fixtures locais foram usados para validação.

Versões efetivamente conferidas: Python 3.11.9, PySide6 6.11.2, yt-dlp 2026.8.19, PyInstaller 6.22.3 e JDK 17. Configuração Android: AGP 9.4.0, Gradle 9.6.0, compile/target/min SDK 36/35/29; wrapper 0.18.1. A stack foi mantida.

## Mapa e contratos do projeto

- Desktop: dois entrypoints `baixar_musica_qt.py`; Qt/PySide6, `DownloadWorker` em QThread, yt-dlp e pós-processamento FFmpeg. Preferências em QSettings, destinos escolhidos pelo usuário e cookies externos opcionais.
- Compartilhado: `media_sources.py` e `resources/sources.json` definem classificação, allowlist, aliases, seleção de vídeos/índices e mensagens; `metadata_ipc.py` usa processo cancelável e socket local, inclusive no EXE sem console.
- Android: MainActivity em Java, executores de download/imagem/metadados, SourcePolicy e MediaMetadata; SharedPreferences, cache temporário e publicação final no MediaStore. Identidade/assinatura mantidas.
- Fluxos documentados e confirmados no código: colar URL, prévia opcional, selecionar vídeo/todos, seis formatos, intervalo GIF de até 30 s, playlists YouTube, progresso/pós-processamento, falhas parciais e acesso ao resultado. Temas claro/escuro e maximização desktop normal persistem.
- Não há serviço backend próprio remoto, banco de dados próprio, fila/histórico, cancelamento de conversão ou login integrado. Autenticação externa, compatibilidade dos sites e disponibilidade da mídia dependem das integrações existentes.

## Cobertura da inspeção

`Inspecionado` significa leitura da implementação completa pela equipe de auditoria, incluindo consumidores pertinentes; busca de nomes sozinha não foi contabilizada. A validação abaixo corresponde à revisão atual, não aos relatos históricos.

| Área | Inventariado e inspecionado | Alterado | Validado nesta auditoria | Pendente |
| --- | --- | --- | --- | --- |
| Windows desktop | Entry point inteiro: opções/erros/fallbacks, worker, UI, estilos/pintura, prévia, thumbnail, preferências/lifecycle | Opções, normalizador e cálculos de progresso | Testes, comparação com fonte inicial, conversões/capas/posts, janela nativa, EXE/IPC | Instalação limpa e matriz ampla de DPI |
| Linux desktop | Entry point byte-idêntico ao Windows, scripts/spec/README/configs próprios lidos | Mesmo lote do Windows | Fonte nos testes Windows; equivalência binária dos dois fontes | Build, sessão gráfica e instalação Linux atuais |
| Módulos raiz e catálogo | `media_sources.py`, `metadata_ipc.py`, `resources/sources.json` completos | Preservados | Classificação/redirects/seleção/erros e IPC offline empacotado | Disponibilidade real de todos os sites |
| Android Java | MainActivity, MediaMetadata, SourcePolicy, MediaBackgroundDrawable, ThumbnailBlur completos | MainActivity | Checks Java, assembleDebug, lintDebug e APK | Aparelho físico, MediaStore e aparência nesta revisão |
| Android recursos/configuração | Manifest, cinco XML de recursos, Gradle/settings/properties e configuração wrapper completos | Preservados | Build/lint/recursos APK | Release/assinatura e instalação não executadas |
| Android scripts | Seis scripts próprios de setup/build/instalação PS/Bash completos | Builds PS debug/release | Parser PowerShell e build Gradle debug | Fluxos release/adb deliberadamente não executados |
| Scripts Python | Os dez scripts originais inteiros; novo `java_support.py` revisado | Dois verificadores Java e helper | Ambos por arquivo e por módulo; JDK válido/inválido; conversões/inspectores | Validação optativa de rede não executada |
| Empacotamento desktop | Dois specs, helper, build Windows/Linux, install/run Linux e Inno completos | Preservados | PyInstaller Windows e recursos; scripts analisados | Pacote Linux, instalador Inno e instalação atuais |
| Testes/fixtures | Dois testes Python, dois testes Java e casos JSON completos | Dois testes Python e SourcePolicyCheck | 27 testes Python; 41 URLs + 8 normalizações + 90 casos de arquivos Java; blur CPU | Cobertura de dispositivo/plataforma não substituída por testes host |
| Configuração/docs | Requirements, ignore/attributes, CI/templates, READMEs, BUILD/DEPENDENCIES/SOURCES/VALIDATION/ROADMAP, documentos/prompts de design completos | Este relatório | `pip check`, diff e análise dos consumidores/comandos | CI remoto da limpeza não executado |
| Assets/licenças/terceiros | Imagens/ícones/licenças inventariados e referências conferidas; wrappers Gradle/geradores e integrações examinados | Preservados | Recursos presentes no build | Imagens históricas não passaram por nova revisão visual individual; implementação de terceiros fora do escopo |

Não restou módulo de implementação própria pendente de leitura. Dependências instaladas, ferramentas binárias, JAR do wrapper, caches, outputs, `.venv`, `work` e arquivos de autenticação/assinatura não foram tratados como código descartável. O inventário complementar não encontrou outro fonte próprio ativo fora dos arquivos versionados. Configurações locais sensíveis não foram exibidas.

## Lotes executados e evidências

| Classe/localização | Problema e evidência antes da mudança | Alteração e benefício | Risco e validação |
| --- | --- | --- | --- |
| B — ambos desktops, `criar_opcoes_download` | Template de título repetido em cada rota; MP4/duas rotas fallback/MKV repetiam remux e opções comuns | Template comum e bloco de remux, mantendo seletor compat, cliente android_vr, container e cópias dos pós-processadores | Caracterização antes/depois, 48 combinações comparadas com cópia inicial, conversões/capas/posts reais locais |
| B — desktop, `normalizar_url` | Mesma regra trim/inclusão HTTPS já existe em `media_sources.normalize_url` | Delegação mantendo wrapper público e assinatura `normalizar_url(url=...)` | Revisão independente detectou incompatibilidade do alias inicialmente proposto; corrigida antes da entrega e coberta por assertion |
| A — desktop, progress hook | Bytes totais/baixados eram calculados duas vezes a partir do mesmo payload | Reutiliza os valores já calculados | Testes de progresso/metadata, streams desconhecidos e pós-processamento |
| A/B — MainActivity | Import FFmpeg sem referência; normalizador privado idêntico a SourcePolicy; oito chamadas de updateStatus sempre passam true | Remove import/método privado e booleano desnecessário; usa política existente e status indeterminado igual | 8 entradas normalizadas; compile/lint; mensagens e atualização na UI thread preservadas |
| A — MainActivity, `listOutputFiles` | `finalOutput` já normaliza caixa e rejeita `.temp.`/`.part.`; sufixos `.part`, `.ytdl`, `.temp`, `.tmp` não terminam em um dos seis formatos | Remove verificações redundantes; conserva extensão final, tamanho positivo, coleta e ordenação | 90 casos entre seis formatos, caixa alta, finais e intermediários; checks antes/depois |
| A — builds Android PS | `setup_android.ps1` já resolve ANDROID_HOME ou lança; bloco posterior só poderia executar se setup tivesse prosseguido sem sua garantia | Remove fallback inalcançável em debug/release | Leitura de setup, parser dos scripts e build debug; release não executado |
| B — verificadores Java | Mesma descoberta JAVA_HOME/PATH/javac/runtime em dois scripts | Helper específico somente para descoberta; compilação/execução permanecem nos consumidores | Entrada por arquivo/módulo, prioridade do JDK e mensagens originais de erro preservadas; sucesso e JDK inválido verificados |
| Apoio de validação — PostUITests | Três casos criavam janela com QSettings real, ao contrário dos testes desktop já isolados | INI temporário por teste, sem enfraquecer assertions | Suíte completa passou; evita gravar preferências reais nas próximas execuções |

As implementações de UI não foram unificadas nem redesenhadas. Não houve alteração nos schemas/catalogue, manifestos de dependência, versões, protocolos IPC, formatos persistidos, assinatura ou applicationId.

## Validação e limites

| Verificação | Antes | Depois |
| --- | --- | --- |
| `python -m unittest discover -s tests -v` | 26 testes OK, 8.272 s | 27 testes OK, 8.040 s |
| Caracterização remux/fallback | Novo caso passou antes de refatorar em ambos desktops | Passou na suíte final; inclui isolamento de dicts/extração/post/keyword público |
| `python scripts/validate_media.py` | Passou | Passou: 6 formatos + WEBM vindo de MP4; vídeo/áudio/codecs/duração conferidos por FFprobe |
| Capas no mesmo verificador | Passou | 6 cenários MP4/MKV, JPEG/WebP/falha/ausência; hashes dos streams preservados e sem sidecars |
| `python scripts/validate_posts.py` | Passou | Segundo vídeo, todos e falha parcial passaram; 1/3/2 arquivos finais com nomes distintos |
| Checks Java fontes/blur | 41 URLs e blur passaram | 41 URLs, 8 normalizações, 90 arquivos e blur passaram; checks ampliados também passaram antes da alteração Android |
| Entrada dos verificadores Java | Documentada por arquivo | Arquivo e `python -m scripts...` passaram; JAVA_HOME inválido retorna código 1 e mensagem original |
| Gradle `assembleDebug lintDebug` | Passou, 15 s; 0 erros/22 avisos | Passou, 38 s; 0 erros/22 avisos |
| `python scripts/check_apk.py ...` | Artefato baseline disponível | Passou: quatro ABIs, EJS/ferramentas/catálogo; fallback yt-dlp 2025.11.12 |
| PyInstaller Windows `--clean` | Binário histórico não usado como prova atual | Passou, cerca de 109 s; saída separada em `baixarMusicaYouTube/dist/audit/baixar_musica_qt.exe` |
| `python scripts/check_bundle.py --executable ...` | — | Passou: ferramentas/EJS/capas/TLS/licenças; sem cookies/DLLs de sistema indevidas |
| Verificação offline contra backup | — | 48 combinações de opções equivalentes e normalizador nomeado; ranges GIF avaliados |
| Interface Windows pelo fonte | — | Abriu maximizada normalmente; janela 800×600 em dois temas inspecionada, 192 famílias de fontes; INI temporário |
| EXE sem console / IPC | — | Helper empacotado iniciou, respondeu por socket local e encerrou com 0, usando URL rejeitada sem rede/sem QSettings |
| `python -m pip check` / `git diff --check` | Passaram | Passaram; sem upgrades ou nova dependência |

O HTTP 404 na fixture de falha parcial e nos cenários de capa indisponível é esperado e foi seguido pelas assertions correspondentes. Gradle já emitia aviso de recursos depreciados. Lint conserva 22 avisos de tradução/configuração/versões; eles não foram desabilitados. Avisos LF/CRLF do Git decorrem das regras existentes; nenhuma reformatização global foi aplicada. Uma execução isolada da suíte de fontes emitiu ResourceWarning de quatro objetos no encerramento, sem falha; a suíte integrada final não reproduziu esse aviso.

O baseline executou os testes antigos antes de descobrir que PostUITests gravava tema/geometria em QSettings real. Esses testes podem ter modificado preferências de janela; os valores anteriores não foram capturados, então não foi inventada uma restauração. O harness foi isolado. A validação nativa posterior usou somente preferências temporárias.

Linux real, Android físico, instalação limpa, release/assinatura, Inno e CI remoto não foram executados. Sites externos não foram consultados. A revisão atual não confirma a disponibilidade de TikTok/Twitch VOD nem todos os dispositivos/DPIs/leitores de tela. O EXE foi testado via helper IPC; a janela nativa inspecionada foi a execução pelo fonte. Estes limites não impedem os lotes locais de limpeza comprovados e não são alegação de equivalência universal ou ausência de bugs.

## Preservados e achados independentes

- **C — contratos públicos:** `caminho_icone`, constantes/exports e método de cancelamento não têm consumidor interno atual em certos caminhos, mas não há evidência sobre consumidores externos. Preservados; remover exigiria verificar usos externos/decisão de compatibilidade.
- **C — empacotamento:** hiddenimports/excludes e dependências extras têm carregamento dinâmico ou papel em EJS, TLS, capas e wrapper Android. Não são removíveis por busca textual. Specs semelhantes preservados; consolidá-los exigiria validação de build Linux atual.
- **Mantidos por responsabilidade comprovada:** NoRedirect, assinatura `media_filter(incomplete=...)`, SilentLogger, referência QCoreApplication no helper, cancelamento/generation/timeouts, estados de prévia, fallback backend, índices descontínuos e ícones normal/round. Pequena duplicação entre plataformas preserva fronteiras diferentes.
- **D — Android/MediaStore:** `publishToDownloads` pode deixar URI com IS_PENDING=1 se abrir/copiar/fechar falhar. Precisa definir e testar cleanup após erro, idealmente em aparelho/emulador.
- **D — Android instalação:** script PS não verifica LASTEXITCODE após `adb install` antes da mensagem de sucesso. Precisa correção funcional e teste com ADB simulado/real sem instalar inadvertidamente.
- **D — parser GIF Android:** aceita componentes como `1:-10` ou `1:`; a validação estrita de componentes diverge do desktop. Precisa decidir contrato de entradas e testar, sem misturar com a limpeza.
- **D — Linux launcher:** Exec do `.desktop` não protege caminhos com espaços; requer teste Linux em HOME contendo espaços.
- **D — API Python:** `resolve_url('t.co/abc')` classifica como válido, mas cria Request com a entrada original sem esquema. Reproduzido com opener falso, sem rede; a GUI normaliza antes. Corrigir altera o comportamento público e ficou separado.
- **Docs históricas:** abertura de CONTRIBUTING/README Linux ainda trata redesign/fontes como etapas futuras. Não foram reescritas as instruções/histórico para facilitar a auditoria; sincronização editorial pode ser feita separadamente.

Nenhuma suspeita C foi convertida em exclusão sem prova. Nenhum achado D de produto foi implementado como se fosse limpeza.

## Métricas, estado e reversão

- Código de aplicação: redução líquida de **68 linhas** (25 em cada desktop e 18 em MainActivity).
- Scripts: redução líquida de **6 linhas**, incluindo as 14 linhas do helper novo.
- Testes: acréscimo líquido de **104 linhas**; assertions antigas mantidas, novos riscos cobertos e preferências isoladas.
- Dependências removidas/adicionadas: **0**. Não há arquivo de aplicação inteiro excluído. Nenhuma saída gerada foi editada manualmente ou entrou no diff; EXE/APK/caches/fixtures foram regenerados para validação e continuam ignorados.
- Git final: dez arquivos existentes modificados e dois novos (`scripts/java_support.py`, este relatório); índice vazio. Todas as mudanças de fonte são desta tarefa, pois a referência inicial estava limpa. Ambos desktops continuam byte-idênticos.

A pasta externa desta auditoria contém `before/`, logs, capturas, inventário/cobertura, manifesto de hashes e `revert_cleanup.py`. O script faz somente leitura por padrão; com `--apply`, restaura os arquivos modificados da cópia inicial e remove somente os dois arquivos novos desta tarefa. Ele recusa se HEAD mudou, se houver stage ou se algum arquivo do lote não corresponder ao hash final, protegendo edições posteriores. Não usa reset/checkout/clean nem altera arquivos alheios.

Para voltar ao fonte anterior, execute o script externo primeiro sem argumentos e depois com `--apply`. Os caminhos locais exatos e o comando estão na memória global do projeto e na entrega do chat, fora deste relatório versionável. A reversão cobre o código/docs; artefatos ignorados podem ser regenerados pelo build a partir do fonte restaurado. A cópia externa existe neste computador; retenção em outro ambiente depende de preservá-la.

Próximos passos reais: revisar o diff local; testar esta revisão no Android e Linux antes de distribuição; tratar separadamente os achados funcionais D. Commit/push/distribuição dependem de autorização específica.
