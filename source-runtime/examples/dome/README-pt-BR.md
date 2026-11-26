# Exemplo de cúpula oca

Inicie o FullArcCAD antes de abrir `Hollow-dome-demo.FCStd` e salve uma cópia de trabalho. As dimensões iniciais são base de 30 × 42 mm, altura de 12 mm e parede de 1 mm, com fundo aberto.

Altere `BaseX`, `BaseY`, `DomeRise` e `Wall` em Alterar parâmetros. Defina `Wall` como 0 mm para uma cúpula sólida. Os campos vinculados estão desabilitados no editor de dimensões. Para editar um de forma independente, escolha Valor fixo (sem expressão) em Atribuições de cotas e aplique; seu valor atual é mantido.

O volume do material é medido a partir da forma real visualizada em mm³, excluindo a cavidade oca. Não é peso. Ele é atualizado com dimensões e desaparece em visualizações inválidas. Use o limite de parede exibido ao ajustar as dimensões.

A posição X/Y/Z coloca o centro da base; a edição preserva a rotação existente. A posição dentro de uma peça pai usa seu sistema de coordenadas. Cancelar remove a visualização e restaura a visibilidade da fonte.
