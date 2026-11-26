# Modifier l’exemple d’ellipses numériques

Démarrez FullArcCAD, ouvrez `Positioned-ellipses-demo.FCStd` et enregistrez une copie de travail. L’exemple contient deux ellipses de 40 × 20 mm extrudées sur 8 mm, initialement centrées en X −35/+35 mm et Y 10 mm.

Dans «Modifier les paramètres», faire passer `Gap` de 70 à 100 mm déplace les centres à −50/+50 mm. `Width`, `Height` et `CenterY` contrôlent les deux ellipses. La largeur et la hauteur sont des dimensions totales, pas des rayons.

Pour modifier uniquement l’ellipse gauche, réglez ses affectations `EllipseCenterX` et `EllipseWidth` sur **Valeur fixe (sans expression)**, puis appliquez. Les valeurs actuelles sont conservées. Modifiez l’esquisse, utilisez **Déplacer le centre de l’ellipse** pour régler X sur −50 mm, puis **Redimensionner l’ellipse** pour régler sa largeur sur 50 mm. Conservez les valeurs liées de Y et de hauteur. Les extrusions existantes sont actualisées ; l’ellipse droite conserve sa largeur. Les changements ultérieurs de `Gap` affectent uniquement le centre droit, qui reste lié.

Les champs liés sont désactivés. Supprimez les deux liaisons de coordonnées pour activer «Placer à l’origine». Les coordonnées sont locales à l’esquisse. Recréez l’ellipse pour permuter les axes majeur et mineur ou utiliser des dimensions égales. Les modifications indépendantes, Annuler/Rétablir et l’enregistrement suivi d’une réouverture ont été vérifiés à l’origine sur une copie ; les originaux fournis restent inchangés.

S’il y a plusieurs ellipses, sélectionnez un contour pris en charge avant d’ouvrir l’éditeur pour en faire la cible initiale. Les axes de construction et les ellipses ordinaires ne comptent pas comme une sélection d’ellipse numérique. Si plusieurs contours compatibles sont sélectionnés, le premier de la liste est utilisé.
