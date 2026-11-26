# Exemple de dôme creux

Démarrez FullArcCAD, ouvrez `Hollow-dome-demo.FCStd` et enregistrez une copie de travail. Les dimensions initiales sont une base de 30 × 42 mm, une hauteur de 12 mm et une épaisseur de paroi de 1 mm. Le dessous est ouvert.

Modifiez `BaseX`, `BaseY`, `DomeRise` et `Wall` dans «Modifier les paramètres». Avec `Wall` = 0 mm, le dôme est plein. Les champs liés sont désactivés dans l’éditeur de cotes. Pour modifier un champ indépendamment, sélectionnez «Valeur fixe (sans expression)» dans «Affectations des cotes», puis appliquez. La valeur actuelle est conservée.

Le volume de matière est calculé à partir de la géométrie réelle de l’aperçu en mm³, sans inclure la cavité. Il ne s’agit pas d’un poids. Il est actualisé lorsque les dimensions changent et n’est pas affiché si l’aperçu est invalide. Respectez la limite d’épaisseur affichée lors du réglage des dimensions.

La position X/Y/Z définit le centre de la base. La modification conserve la rotation existante. À l’intérieur d’un Part parent, la position utilise le repère de ce parent. «Annuler» supprime l’aperçu et restaure la visibilité de l’original.
