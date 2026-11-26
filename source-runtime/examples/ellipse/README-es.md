# Edición del ejemplo de elipses numéricas

Inicie FullArcCAD, abra `Positioned-ellipses-demo.FCStd` y guarde una copia de trabajo. El ejemplo contiene dos elipses de 40 × 20 mm extruidas 8 mm. Inicialmente, sus centros están en X −35/+35 mm e Y 10 mm.

En «Modificar parámetros», cambiar `Gap` de 70 a 100 mm sitúa los centros en −50/+50 mm. `Width`, `Height` y `CenterY` controlan ambas elipses. Anchura y altura son dimensiones completas, no radios.

Para modificar solo la elipse izquierda, establezca sus asignaciones `EllipseCenterX` y `EllipseWidth` en **Valor fijo (sin expresión)** y aplique. Los valores actuales se conservan. Edite el croquis, utilice **Mover centro de elipse** para establecer X en −50 mm y después **Cambiar tamaño de elipse** para establecer la anchura en 50 mm. Mantenga los valores vinculados de Y y altura. Las extrusiones existentes se actualizan y la elipse derecha conserva su anchura. Los cambios posteriores de `Gap` afectan solo al centro derecho, que sigue vinculado.

Los campos vinculados están desactivados. Desvincule ambas coordenadas para activar «Llevar al origen». Las coordenadas son locales al croquis. Cree de nuevo la elipse para intercambiar los ejes mayor y menor o utilizar dimensiones iguales. La edición independiente, Deshacer/Rehacer y guardar/reabrir se verificaron originalmente en una copia; los originales suministrados no se modifican.

Si hay varias elipses, seleccione un contorno compatible antes de abrir el editor para utilizarlo como objetivo inicial. Los ejes de construcción y las elipses normales no cuentan como elipses numéricas. Si hay varios contornos compatibles seleccionados, se usa el primero de la lista.
