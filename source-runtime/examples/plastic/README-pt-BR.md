# Caixa de plástico: edição e exportação

Inicie o FullArcCAD antes de abrir um exemplo e salve uma cópia de trabalho. `Parametric-enclosure.FCStd` demonstra cotas vinculadas de ressaltos de fixação, furos passantes, reforços triangulares e ganchos de encaixe. `Drafted-enclosure.FCStd` adiciona ângulos de saída aos ressaltos. `Instanced-enclosures.FCStd` utiliza a mesma caixa em dois componentes posicionados. `Tapered-rib-demo.FCStd` demonstra ângulos de saída em nervuras e ressaltos e a altura vinculada dos ganchos de encaixe.

Em Alterar parâmetros, defina `BossHeight` como 18 mm no exemplo paramétrico. A altura de encaixe dependente passa a ser 20 mm. Desfazer/Refazer restaura ambos juntos. Salve e reabra para manter dimensões e expressões.

Use Gerenciar para exportar STEP/STL; a exportação inclui geometria visível, portanto, verifique a visibilidade do recurso final ao inspecionar recursos históricos. Use Projeto → Renderização para um PNG isométrico. O fluxo de trabalho verificado preserva a câmera, a seleção, a visibilidade e o histórico durante a geração da imagem. A reimportação STEP corresponde ao volume e aos limites do material editado. Edite recursos plásticos do histórico; os campos vinculados são ajustados através de Alterar Parâmetros.
