# Fundo com a thumbnail — revisão 04

Implementação aprovada em 2026-10-04, nas três interfaces. Complementa o [projeto visual](PROJETO_UI.md); as paisagens dos conceitos anteriores continuam sendo ilustrações.

## Aparência

- Usar a thumbnail original já carregada. A miniatura do painel permanece nítida, com proporção preservada.
- Fundo em toda a área interna, com recorte central proporcional que preenche a janela. Nunca esticar a imagem ou alterar a moldura nativa/maximização normal.
- Cópia reduzida até 640 px no maior lado, desfoque suave de raio 3 px, preparado uma vez. Qt usa efeito nativo em uma imagem fora da tela; Android usa filtro CPU de duas passagens no executor de imagens. A intensidade visual varia entre os filtros nativos, sem exigir pixels idênticos entre plataformas.
- Camada do gradiente atual: azul a 68% de opacidade no escuro; branca/perolada a 78% no claro.
- Painéis na cor existente, alpha 214/255 (aproximadamente 84%). Campos e botões mantêm fundos opacos. Apenas legendas pequenas sobre a imagem passam a branco no escuro e texto escuro no claro, para proteger a leitura nas fotos extremas.
- Entrada de 250 ms; depois, fundo estático, inclusive durante rolagem. Android respeita animações desabilitadas pelo sistema. Não há movimento contínuo/parallax.

![Tema escuro — captura Windows](../images/ui-fundo-escuro.png)

![Tema claro — captura Windows](../images/ui-fundo-claro.png)

São capturas reais da prévia de um vídeo público antes de iniciar o download, com progresso em 0%. Não são mockups ou evidência de teste em Linux/Android.

## Comportamento e custo

O efeito reutiliza a requisição e a decodificação da thumbnail. Não consulta outro serviço, não muda dependências e não interfere no download, conversão ou capa incorporada. Tema e tamanho apenas repintam/reenquadram a cópia; não reaplicam o desfoque. O fundo fica atrás dos controles, sem desfocar a árvore da interface.

Editar/apagar o link libera a imagem imediatamente. Respostas obsoletas não podem restabelecer o fundo anterior. Ao começar o download, a prévia disponível é mantida; em playlists, os metadados da mídia atual conduzem a troca. Fechar libera imagem/animação e cancela as consultas existentes. Sem imagem ou se a preparação falhar, usar o gradiente anterior com painéis opacos, silenciosamente.

## Validação atual

Quinze regressões desktop passaram para ambos os fontes, incluindo cache, bordas, desfoque, original preservado, recorte vertical/horizontal, transição para download, falha opcional e contraste de texto sobre imagens preta/branca (4,5:1 para legendas pequenas e textos dos painéis). Qt nativo Windows foi conferido nos dois temas e escalas 100/125/150/200%; fundo fixo na rolagem e controles sem rolagem horizontal.

Filtro CPU Android passou em JDK 17 com dimensões estreitas, transparência, bordas, cores sólidas, entrada inválida e cache 640 × 640. Isso verifica a matemática, não a renderização no celular. Builds Windows/instalador/APK debug e conferência de recursos passaram. [Validação](../VALIDATION.md) mantém evidências e limitações; Android físico, Linux gráfico e CI desta revisão permanecem pendentes.
