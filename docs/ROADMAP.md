# Roteiro / Roadmap

## Base pública v3

Organização do repositório, GPLv3, documentação bilíngue e transparência sobre produção por IA; atualização de dependências e empacotamento sem sessões pessoais. Interface e YouTube mantidos. Base registrada pelo mantenedor no commit `b6bc4f6` (2026-10-04). Windows e Linux passaram no CI; o ajuste do workflow Android aguarda nova execução.

## Nova interface — implementada

O mantenedor aprovou temas claro/escuro e maximização normal, preservando a barra de tarefas. Implementação Windows/Linux e adaptação Android concluídas, com seis formatos, preferência de tema, painel de andamento e thumbnail original opcional. Capturas reais e limites estão em [Validação](VALIDATION.md); mockups/especificação em [Projeto UI](design/PROJETO_UI.md).

O mantenedor confirmou funcionamento no celular. Antes de distribuir: ampliar a cobertura Android por dispositivo/site/formato, conferir Linux gráfico, instalação Windows e o CI desta revisão depois do commit/push do mantenedor.

Prévia automática e fundo com a thumbnail também implementados, com falhas silenciosas e temas adaptados. A [especificação do fundo](design/FUNDO_THUMBNAIL.md) registra opacidades, cache, comportamento e limites da validação.

## Outras fontes — integradas

Instagram, X/Twitter, Facebook, Twitch e TikTok experimental foram adicionados ao catálogo compartilhado, com prévia silenciosa, escolha individual/todos em posts e conversão WEBM quando necessária. Amostras públicas de quatro novas fontes passaram no Windows; resultados e limites por plataforma estão em [Fontes](SOURCES.md) e [Validação](VALIDATION.md).

## Próximos passos reais

1. Detalhar a cobertura Android após o teste bem-sucedido relatado pelo mantenedor; conferir Linux gráfico/build e o CI desta revisão depois de seu commit/push.
2. Validar outros exemplos de Facebook, Twitch VOD e TikTok quando o extrator/conectividade permitir.
3. Avaliar novas fontes e tipos de coleção conforme testes; perfis, stories e lives continuam fora desta expansão.

Não há data prometida nem modelo de IA em runtime. Cancelamento de downloads/conversão, atualizações automáticas desktop e unificação da arquitetura Windows/Linux são decisões futuras.

English: V3.3 integrates five new sources with silent previews and individual/all selection for posts. Four Windows samples passed; TikTok remains experimental. The maintainer reported successful Android phone use; detailed Android coverage, Linux graphical/runtime and hosted CI checks remain pending.
