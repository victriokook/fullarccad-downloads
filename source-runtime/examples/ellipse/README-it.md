# Modifica dell'esempio dell'ellisse numerica

Avvia FullArcCAD prima di aprire `Positioned-ellipses-demo.FCStd`, quindi salva una copia di lavoro. L'esempio contiene due ellissi di 40 × 20 mm estruse di 8 mm, inizialmente centrate su X −35/+35 mm e Y 10 mm.

In Modifica parametri, la modifica di `Gap` da 70 a 100 mm sposta i centri a −50/+50 mm. `Width`, `Height` e `CenterY` controllano entrambe le ellissi. La larghezza e l'altezza sono a lunghezza intera.

Per modificare solo l'ellisse sinistra, imposta le sue assegnazioni `EllipseCenterX` e `EllipseWidth` su **Valore fisso (senza espressione)** e applica. Ciò mantiene i loro valori attuali. Accedere alla modifica dello schizzo, utilizzare **Sposta centro ellisse** per impostare la X sinistra su −50 mm, quindi **Ridimensiona ellisse** per impostarne la larghezza su 50 mm. Lasciare invariate la Y e l'altezza collegate. Le estrusioni esistenti vengono aggiornate; l'ellisse destra mantiene la sua larghezza. Le successive modifiche a `Gap` influiscono solo sul centro destro ancora collegato.

I campi collegati sono disabilitati. Rimuovi entrambi i collegamenti di coordinate per abilitare Porta all’origine. Le coordinate sono locali rispetto allo schizzo. Ricrea un'ellisse per scambiare gli assi maggiori/minori o utilizzare dimensioni uguali. Modifiche indipendenti, Annulla/Ripeti e salvataggio/ricaricamento sono stati verificati su una copia; gli originali forniti rimangono invariati.

Con più ellissi, seleziona un contorno supportato nella modifica dello schizzo prima di aprire un editor per inizializzare quella destinazione. Gli assi di costruzione e le ellissi ordinarie non contano come selezione numerica dell'ellisse. Più profili supportati rientrano nel primo elemento dell'elenco.
