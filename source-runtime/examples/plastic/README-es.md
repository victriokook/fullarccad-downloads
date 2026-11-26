# Caja de plástico: edición y exportación

Inicie FullArcCAD antes de abrir un ejemplo y guarde una copia de trabajo. `Parametric-enclosure.FCStd` muestra cotas vinculadas de resaltes de fijación, taladros pasantes, refuerzos triangulares y ganchos de encaje. `Drafted-enclosure.FCStd` añade ángulos de desmoldeo en los resaltes. `Instanced-enclosures.FCStd` comparte la misma caja entre dos componentes colocados. `Tapered-rib-demo.FCStd` muestra ángulos de desmoldeo en nervios y resaltes y una altura de gancho vinculada.

En el ejemplo paramétrico, establezca `BossHeight` en 18 mm mediante «Modificar parámetros». La altura del gancho dependiente pasa a 20 mm. Deshacer/Rehacer restaura ambos cambios conjuntamente. Las cotas y expresiones se conservan al guardar y volver a abrir.

Exporte STEP/STL desde «Gestionar». La exportación incluye la geometría visible: compruebe la visibilidad de la operación final cuando examine operaciones anteriores del historial. Use «Diseño → Renderizado» para generar un PNG isométrico. El flujo verificado originalmente conserva la cámara, la selección, la visibilidad y el historial al generar imágenes; la reimportación STEP coincide en volumen de material y dimensiones exteriores. Edite las operaciones de plástico desde el historial. Ajuste los campos vinculados mediante «Modificar parámetros».
