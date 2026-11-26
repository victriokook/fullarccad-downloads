# Editando o exemplo da elipse numérica

Inicie o FullArcCAD antes de abrir `Positioned-ellipses-demo.FCStd` e salve uma cópia de trabalho. O exemplo contém duas elipses de 40 × 20 mm extrudadas de 8 mm, inicialmente centradas em X −35/+35 mm e Y 10 mm.

Em Alterar parâmetros, alterar `Gap` de 70 para 100 mm move os centros para −50/+50 mm. `Width`, `Height` e `CenterY` controlam ambas as elipses. Largura e altura são comprimentos completos.

Para editar apenas a elipse esquerda, defina suas atribuições `EllipseCenterX` e `EllipseWidth` para **Valor fixo (sem expressão)** e aplique. Isso mantém seus valores atuais. Entre na edição do esboço, use **Mover centro da elipse** para definir o X esquerdo como −50 mm e, em seguida, **Redimensionar elipse** para definir sua largura para 50 mm. Deixe o Y vinculado e a altura inalterados. As extrusões existentes são atualizadas; a elipse direita mantém sua largura. As alterações posteriores de `Gap` afetam apenas o centro direito ainda vinculado.

Os campos vinculados estão desativados. Remova ambas as ligações de coordenadas para ativar Mover para a origem. As coordenadas são locais ao esboço. Recrie uma elipse para trocar eixos maiores/secundários ou usar dimensões iguais. Edições independentes, Desfazer/Refazer e salvar/recarregar foram verificadas em uma cópia; originais fornecidos permanecem inalterados.

Com múltiplas elipses, selecione um contorno suportado na edição de esboço antes de abrir um editor para inicializar esse destino. Eixos de construção e elipses comuns não contam como seleção de elipse numérica. Vários contornos suportados retornam ao primeiro item da lista.
