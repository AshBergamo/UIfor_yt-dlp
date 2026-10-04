# Roteiro / Roadmap

## Base pública v3

Organização do repositório, GPLv3, documentação bilíngue e transparência sobre produção por IA; atualização de dependências e empacotamento sem sessões pessoais. Interface e YouTube mantidos. Base registrada pelo mantenedor no commit `b6bc4f6` (2026-10-04). Windows e Linux passaram no CI; o ajuste do workflow Android aguarda nova execução.

## Nova interface — implementada

O mantenedor aprovou temas claro/escuro e maximização normal, preservando a barra de tarefas. Implementação Windows/Linux e adaptação Android concluídas, com seis formatos, preferência de tema, painel de andamento e thumbnail original opcional. Capturas reais e limites estão em [Validação](VALIDATION.md); mockups/especificação em [Projeto UI](design/PROJETO_UI.md).

Antes de distribuir: conferir a nova UI em Android físico e Linux gráfico, instalação Windows e o CI desta revisão depois do commit/push do mantenedor.

Prévia automática e fundo com a thumbnail também implementados, com falhas silenciosas e temas adaptados. A [especificação do fundo](design/FUNDO_THUMBNAIL.md) registra opacidades, cache, comportamento e limites da validação.

## Próxima etapa — outras fontes

1. Escolher os primeiros sites adicionais e exemplos públicos autorizados para teste.
2. Ampliar URLs para sites suportados pelo yt-dlp, revisando validação, playlists, metadados e mensagens específicas de cada fonte.
3. Validar fontes selecionadas e só então declarar suporte testado. O suporte upstream a milhares de sites não significa que esta interface já aceite ou tenha testado todos eles.

Não há data prometida nem recursos de IA em runtime nesta etapa. Cancelamento, atualizações automáticas desktop e unificação de fontes Windows/Linux são decisões futuras.

English: the baseline was committed and the redesigned UI is now implemented. Device/Linux graphical checks and CI for this revision remain pending. Next, select and validate additional yt-dlp websites; upstream extractor coverage is not equivalent to tested GUI support.
