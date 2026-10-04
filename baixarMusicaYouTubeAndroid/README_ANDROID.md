# UIfor_yt-dlp Android · v3

Aplicativo Java com o backend `youtubedl-android` 0.18.1 e ferramentas nativas FFmpeg, FFprobe, Python e QuickJS. Mantém MP4, MP3, WEBM, MKV, GIF, WAV e playlists YouTube. Saídas em `Downloads/BaixarMusicaYouTube` pelo MediaStore.

A nova apresentação usa temas Claro/Escuro salvos localmente, formatos em botões, painéis separados e intervalo condicional para GIF. O tema muda sem recriar a Activity ou perder o download. A miniatura original é opcional e carregada separadamente, com limites de tempo/tamanho. Ao concluir, o botão abre o último arquivo em um aplicativo compatível.

As áreas das barras do sistema e do teclado são consideradas no layout; rotação mantém a Activity e seus campos. O botão Voltar aguarda uma operação ativa terminar. Build e lint não comprovam comportamento visual ou download no aparelho: essa validação ainda está pendente.

Nos novos downloads MP4 e MKV, o yt-dlp também incorpora a thumbnail original como capa, convertendo-a para JPEG quando necessário. A imagem temporária não é publicada como download separado. A galeria/gerenciador/player decide se mostra essa capa; conferir no aparelho. Os demais formatos mantêm seu comportamento atual.

Ao digitar/colar um link de vídeo completo, uma consulta pública leve busca título e thumbnail após uma pausa de 450 ms, sem iniciar o backend de download. Falhas são silenciosas; editar/apagar o link ou iniciar o download cancela a consulta anterior. A consulta e a imagem usam executores separados do download. A prévia preserva progresso em 0% até o download começar; título/imagem já obtidos são mantidos durante a transição.

A mesma thumbnail preenche o fundo com recorte central proporcional, desfoque suave e camada azul/perolada conforme o tema. Só os painéis ficam translúcidos; controles e miniatura original permanecem nítidos. A cópia reduzida (até 640 px) é preparada no executor de imagens, uma vez por foto, e entra em 250 ms quando animações do sistema estão habilitadas. Tema, rolagem, teclado e rotação não reaplicam o filtro. Trocar/apagar o link limpa o fundo e restaura painéis opacos; falhas do efeito são silenciosas. Build/lint e testes do filtro CPU passaram; a renderização e esses comportamentos ainda precisam de teste no celular.

## Ambiente

- JDK 17, AGP 9.4.0 e Gradle Wrapper 9.6.0 com checksum.
- compileSdk 36, targetSdk 35, minSdk 29 (Android 10+).
- applicationId e assinatura release existentes preservados.
- Bibliotecas do wrapper permanecem intactas; dependências transitivas são revisadas no Gradle do app.

Na raiz do repositório, configure JAVA_HOME para JDK 17 e ANDROID_HOME para o SDK, então rode `baixarMusicaYouTubeAndroid/build_android.ps1` no Windows ou `bash build_android.sh` dentro desta pasta no Linux. Consulte [Build](../docs/BUILD.md) para comandos completos, lint e verificação do APK.

O wrapper configura automaticamente QuickJS. O APK inclui EJS no backend empacotado. O app tenta atualizar yt-dlp no canal estável antes do download e mantém o fallback antigo se a atualização falhar. A versão realmente embutida e os limites da validação estão em [Validação](../docs/VALIDATION.md).

## Assinatura e publicação

APK debug não usa sua chave release. `build_android_release.ps1` mantém o fluxo local de assinatura; guarde `release-signing/` fora do Git. Este trabalho não executa release, instala em celular nem altera sua chave. APK compilado não prova download em aparelho real.

## IA e licença

Este app é produzido principalmente por IA com orientação humana; a história e a distinção em relação às bibliotecas estão no [README português](../README.md) e [English README](../README.en.md). Não há modelo de IA executando downloads. Código GPLv3, com avisos próprios das dependências; GPLv3 e avisos de terceiros entram nos assets do APK.
