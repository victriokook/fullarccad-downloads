# Das Beispiel mit numerisch definierten Ellipsen bearbeiten

Starten Sie FullArcCAD, öffnen Sie `Positioned-ellipses-demo.FCStd` und speichern Sie eine Arbeitskopie. Das Beispiel enthält zwei Ellipsen mit 40 × 20 mm, die 8 mm weit extrudiert sind. Ihre Mittelpunkte liegen anfangs bei X −35/+35 mm und Y 10 mm.

Wenn Sie unter „Parameter ändern“ den Wert `Gap` von 70 auf 100 mm ändern, verschieben sich die Mittelpunkte auf −50/+50 mm. `Width`, `Height` und `CenterY` steuern beide Ellipsen. Breite und Höhe sind volle Abmessungen, keine Radien.

Um nur die linke Ellipse zu bearbeiten, setzen Sie deren Zuweisungen `EllipseCenterX` und `EllipseWidth` auf **Fester Wert (ohne Ausdruck)** und wenden die Änderung an. Die aktuellen Werte bleiben erhalten. Wechseln Sie in die Skizzenbearbeitung. Setzen Sie mit **Ellipsenmittelpunkt verschieben** den linken X-Wert auf −50 mm und anschließend mit **Ellipse skalieren** die Breite auf 50 mm. Lassen Sie die verknüpften Werte für Y und Höhe unverändert. Vorhandene Extrusionen werden aktualisiert; die rechte Ellipse behält ihre Breite. Spätere Änderungen an `Gap` betreffen nur den weiterhin verknüpften rechten Mittelpunkt.

Verknüpfte Felder sind deaktiviert. Lösen Sie beide Koordinatenzuweisungen, um „Auf Ursprung setzen“ zu aktivieren. Die Koordinaten gelten im lokalen Skizzensystem. Erstellen Sie die Ellipse neu, wenn Sie Haupt- und Nebenachse vertauschen oder gleiche Abmessungen verwenden möchten. Unabhängige Änderungen, Rückgängig/Wiederholen sowie Speichern und erneutes Öffnen wurden ursprünglich an einer Kopie geprüft; die mitgelieferten Originale bleiben unverändert.

Wählen Sie bei mehreren Ellipsen vor dem Öffnen eines Editors einen unterstützten Umriss in der Skizzenbearbeitung aus. Dieser wird als Anfangsziel verwendet. Konstruktionsachsen und gewöhnliche Ellipsen zählen nicht als numerische Ellipsenauswahl. Bei mehreren unterstützten Umrissen wird der erste Listeneintrag verwendet.
