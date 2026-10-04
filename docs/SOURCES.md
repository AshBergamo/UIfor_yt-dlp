# Fontes integradas / Integrated sources

O catálogo `resources/sources.json` é compartilhado pelos aplicativos desktop e Android. A interface aceita as fontes abaixo; isso não equivale a compatibilidade com qualquer página desses sites. Os [extratores oficiais do yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) mudam conforme os sites mudam.

| Fonte | Links desta etapa | Verificação Windows em 2026-10-04 |
| --- | --- | --- |
| YouTube | Vídeos, Shorts e playlists existentes | Regressão com recorte público de 3 s, vídeo/áudio e capa |
| Instagram | Reels e posts com vídeos | Reel completo de 4,967 s; post com três vídeos; seleção individual e todos |
| X/Twitter | Posts/status com vídeos | Vídeo completo de 3,179 s, com capa |
| Facebook | Vídeos, reels e posts com vídeo | Reel completo de 21,833 s, com capa; outros links podem falhar |
| Twitch | Clips e vídeos gravados (`/videos/`) | Clip completo de 32,099 s, com capa; VOD ainda sem amostra real |
| TikTok | Vídeos individuais | **Experimental**: consultas das amostras falharam com `Unexpected response from webpage request` |

Os downloads públicos foram feitos sem cookies pessoais, com yt-dlp **2026.08.19** e FFmpeg/FFprobe **9.0.2**. A verificação de um exemplo não certifica todos os vídeos, regiões, codecs ou tipos de página. Linux usa o mesmo fonte desktop; execução gráfica/build desta revisão precisam do CI e de um Linux de destino. O mantenedor informou que o aplicativo funcionou no celular em 2026-10-04; não foram detalhados dispositivo, sites ou formatos desse teste. O Android foi compilado e conferido; seu backend empacotado é 2025.11.12, com tentativa de atualização estável antes da primeira consulta ao backend/download. Falhar na atualização pode reduzir a compatibilidade.

## Como usar

Cole o endereço da página do vídeo, escolha o formato e o destino. Após 450 ms sem editar, o app tenta obter título e thumbnail. YouTube usa o oEmbed público; as novas fontes usam uma consulta de metadados pelo backend, sem baixar mídia. A tentativa automática tem prazo de 12 s e falha silenciosamente. Inicialização/atualização Android ocorre em segundo plano e é compartilhada com downloads. Sem prévia, Baixar continua disponível e tenta novamente com prazo maior.

Posts com vários vídeos mostram **Vídeos deste post**: **Todos os vídeos** começa selecionado, com opções para cada vídeo. A capa acompanha a escolha. Se a lista só aparecer depois de clicar em Baixar, escolha os itens e clique novamente; nenhum vídeo começa a ser transferido antes disso. A lista contém vídeos, não fotos. Links do X que apontam explicitamente para `/video/2`, por exemplo, respeitam esse item. Ao baixar todos, os arquivos têm ID/índice no nome; falhas parciais preservam os resultados concluídos e são informadas.

Links curtos reconhecidos, incluindo `vm.tiktok.com`, `vt.tiktok.com`, `t.co` e `fb.watch`, são resolvidos com até cinco redirecionamentos para fontes aceitas. Algumas URLs de compartilhamento não fornecem um redirecionamento utilizável: nesses casos, abra a página e copie seu endereço direto. Perfis inteiros, stories, novas coleções e transmissões ao vivo não integram esta expansão. Conteúdo que exige login, acesso regional ou que foi removido pode não funcionar.

WEBM prefere streams compatíveis; quando necessário, converte para VP9/Opus, o que pode demorar mais. MP3/WAV exigem uma faixa de áudio. As capas de MP4/MKV são opcionais e sua exibição depende do player/gerenciador. Não há importação automática de cookies do navegador nem novo fluxo de login; a variável desktop opcional já existente permanece externa ao pacote.

## Reproduzir

Na raiz, com o ambiente e ferramentas preparados:

```text
python -m unittest discover -s tests -v
python scripts/validate_media.py
python scripts/validate_posts.py
python scripts/check_android_sources.py
python scripts/validate_sources.py --network
python scripts/validate_sources.py --network --site instagram --full
python scripts/validate_sources.py --network --site instagram --url https://www.instagram.com/p/BQ0eAlwhDrw/ --item 2 --full
python scripts/validate_sources.py --network --site instagram --url https://www.instagram.com/p/BQ0eAlwhDrw/ --full
```

O teste público usa recortes de 3 s por padrão; `--full` transfere a amostra completa. `--item` usa o índice do extrator. Resultados, mídia e diagnósticos sanitizados ficam em `work/validation/`, ignorado pelo Git. Esses testes de rede são optativos e não fazem parte do CI: bloqueios temporários não devem transformar uma regressão local em resultado imprevisível.

## English

The shared catalog integrates YouTube plus Instagram, X/Twitter, Facebook, Twitch and experimental TikTok. Only individual public media links are added; existing YouTube playlists remain available. Profiles, stories, new collections and active live streams are deferred. A working extractor or sample does not guarantee every link.

Automatic previews retain the 450 ms debounce and silent failures. New sources use a cancellable metadata-only backend request with a 12-second deadline, without downloading media or personal cookies. Multi-video posts default to **All videos**, allowing one individual video instead. The cover follows selection. If discovery occurs only after clicking Download, the app shows the choice and waits for another click. Completed files survive partial failures.

Windows samples passed for Instagram, X, Facebook and Twitch; Twitch VOD remains untested. TikTok sample extraction failed and stays experimental. The maintainer reported successful use on a physical Android phone; no device/site/format matrix was supplied. Linux runtime/build and hosted CI remain pending. WEBM conversion uses VP9/Opus when native streams are unavailable and can take longer. Run the opt-in network smoke with `--network`; `--full` downloads complete samples. See [Validation](VALIDATION.md) for measured evidence.
