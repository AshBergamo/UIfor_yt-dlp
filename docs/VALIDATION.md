# Validação / Validation

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
python scripts/check_apk.py baixarMusicaYouTubeAndroid/app/build/outputs/apk/debug/app-debug.apk
```

Builds e preparação de ferramentas estão em [BUILD.md](BUILD.md); versões resolvidas em [DEPENDENCIES.md](DEPENDENCIES.md). Os relatórios e mídias de teste ficam em `work/` local, ignorado pelo Git.

English: local desktop regressions, six real conversions, one public cookie-free YouTube download, Windows packaging and Android debug build/lint passed. The Windows native Qt window was checked. GitHub-hosted Windows and Linux checks passed, including packaging; Android CI failed with exit code 127. The workflow now locates sdkmanager explicitly and separates SDK preparation from the build, but the fix needs a new hosted run. Linux graphical execution, clean installer installation, all DPI settings and physical Android downloads remain pending. Compilation is not device validation or a full security audit.
