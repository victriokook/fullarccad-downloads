# Ejemplo de cúpula hueca

Inicie FullArcCAD, abra `Hollow-dome-demo.FCStd` y guarde una copia de trabajo. Las dimensiones iniciales son una base de 30 × 42 mm, una altura de 12 mm y un espesor de pared de 1 mm. La parte inferior está abierta.

Modifique `BaseX`, `BaseY`, `DomeRise` y `Wall` en «Modificar parámetros». Con `Wall` = 0 mm se obtiene una cúpula maciza. Los campos vinculados están desactivados en el editor de cotas. Para editar uno de forma independiente, seleccione «Valor fijo (sin expresión)» en «Asignaciones de cotas» y aplique el cambio; se conserva el valor actual.

El volumen de material se calcula a partir de la geometría real de la vista previa en mm³, sin incluir la cavidad. No representa el peso. Se actualiza al modificar las dimensiones y no se muestra si la vista previa no es válida. Al ajustar las dimensiones, respete el límite de espesor indicado.

La posición X/Y/Z sitúa el centro de la base. La edición conserva la rotación existente. Dentro de un Part padre se utiliza su sistema de coordenadas. «Cancelar» elimina la vista previa y restaura la visibilidad del original.
