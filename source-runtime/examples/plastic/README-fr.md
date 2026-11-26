# Boîtier en plastique : modification et exportation

Démarrez FullArcCAD avant d’ouvrir un exemple et enregistrez une copie de travail. `Parametric-enclosure.FCStd` présente des cotes liées pour les bossages de fixation, trous débouchants, goussets triangulaires et crochets d’encliquetage. `Drafted-enclosure.FCStd` ajoute une dépouille aux bossages. `Instanced-enclosures.FCStd` utilise le même boîtier dans deux composants positionnés. `Tapered-rib-demo.FCStd` présente des dépouilles sur les nervures et bossages, ainsi qu’une hauteur de crochet liée.

Dans l’exemple paramétrique, réglez `BossHeight` sur 18 mm avec «Modifier les paramètres». La hauteur du crochet dépendant devient 20 mm. Annuler/Rétablir restaure les deux ensemble. L’enregistrement et la réouverture conservent les cotes et les expressions.

Exportez en STEP/STL depuis «Gérer». L’exportation inclut la géométrie visible : vérifiez la visibilité de la fonction finale lorsque vous examinez des fonctions antérieures de l’historique. Utilisez «Conception → Rendu» pour créer un PNG isométrique. Le processus vérifié à l’origine conserve la caméra, la sélection, la visibilité et l’historique pendant la génération d’images ; la réimportation STEP correspond au volume de matière et aux dimensions extérieures modifiés. Modifiez les fonctions plastiques depuis l’historique et les champs liés avec «Modifier les paramètres».
