# Involucro in plastica: modifica ed esportazione

Avvia FullArcCAD prima di aprire un esempio e salva una copia di lavoro. `Parametric-enclosure.FCStd` mostra quote collegate di risalti di fissaggio, fori passanti, rinforzi triangolari e ganci a scatto. `Drafted-enclosure.FCStd` aggiunge angoli di sformo ai risalti. `Instanced-enclosures.FCStd` utilizza lo stesso involucro in due componenti posizionati. `Tapered-rib-demo.FCStd` mostra lo sformo di nervature e risalti e l’altezza collegata dei ganci a scatto.

In Modifica parametri, impostare `BossHeight` su 18 mm nell'esempio parametrico. L'altezza dello snap dipendente diventa 20 mm. Annulla/Ripeti ripristina entrambi insieme. Salva e riapri per conservare dimensioni ed espressioni.

Utilizzare Gestisci per esportare STEP/STL; l'esportazione include la geometria visibile, quindi controlla la visibilità della feature finale quando controlli le feature storiche. Usa Progettazione → Rendering per un PNG isometrico. Il flusso di lavoro verificato preserva la fotocamera, la selezione, la visibilità e la cronologia durante la generazione delle immagini. La reimportazione STEP corrisponde al volume e ai limiti del materiale modificato. Modifica le caratteristiche plastiche dalla cronologia; i campi collegati vengono regolati tramite Modifica parametri.
