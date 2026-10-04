# Contribuir / Contributing

Obrigado por contribuir. Antes de mudar o comportamento, descreva o problema, a plataforma e como reproduzi-lo. Esta base mantém a UI atual e YouTube; redesign e novos sites ficam para a etapa seguinte.

- Use ambientes locais isolados e as dependências compartilhadas da raiz.
- Mantenha Windows, Linux e Android identificados: corrigir uma versão não corrige automaticamente as demais.
- Preserve os seis formatos, playlists, validação GIF e mensagens de progresso. Não altere o código das dependências externas.
- Não inclua cookies, credenciais, chaves de assinatura, binários, caches ou caminhos pessoais em commits, screenshots ou logs.
- Produção com IA é parte principal deste projeto. Descreva o que mudou e como foi verificado; identifique simulação, build, execução gráfica e aparelho físico separadamente.
- Rode `python -m unittest discover -s tests -v`; para validar conversões, `python scripts/validate_media.py`. Instale previamente as ferramentas conforme o README.
- Para mudanças Android, rode build debug e lint com JDK 17. Consulte `docs/BUILD.md`.

As contribuições para o código do aplicativo usam GPLv3. Relatos de bug devem informar plataforma, versão, formato, comportamento esperado e observado, sem compartilhar sessão de login.

English: describe the issue, platform and reproduction before changing behavior. Keep changes focused, preserve existing formats, and report actual validation honestly. Do not commit credentials or generated files. Contributions to application code use GPLv3. AI-generated contributions follow the same checks as other contributions.
