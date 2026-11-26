# Esempio di cupola cava

Avvia FullArcCAD prima di aprire `Hollow-dome-demo.FCStd` e salva una copia di lavoro. Le dimensioni iniziali sono una base 30×42 mm, altezza 12 mm e parete 1 mm, con fondo aperto.

Modificare `BaseX`, `BaseY`, `DomeRise` e `Wall` in Modifica parametri. Impostare `Wall` su 0 mm per una cupola solida. I campi collegati sono disabilitati nell'editor delle dimensioni. Per modificarne uno in modo indipendente, scegli Valore fisso (senza espressione) in Assegnazioni delle quote e applica; il suo valore attuale viene mantenuto.

Il volume del materiale viene misurato dalla forma effettiva dell'anteprima in mm³, esclusa la cavità cava. Non è peso. Si aggiorna con le dimensioni e scompare in caso di anteprime non valide. Utilizzare il limite dello spessore della parete visualizzato durante la regolazione delle dimensioni.

La posizione X/Y/Z posiziona il centro della base; la modifica preserva la rotazione esistente. La posizione all'interno di una parte genitore utilizza il suo sistema di coordinate. Annulla rimuove l'anteprima e ripristina la visibilità dell'origine.
