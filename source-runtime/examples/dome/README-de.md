# Beispiel: Hohlkuppel

Starten Sie FullArcCAD, öffnen Sie `Hollow-dome-demo.FCStd` und speichern Sie eine Arbeitskopie. Die Ausgangsmaße sind 30 × 42 mm Grundfläche, 12 mm Höhe und 1 mm Wandstärke. Die Unterseite ist offen.

Ändern Sie `BaseX`, `BaseY`, `DomeRise` und `Wall` unter „Parameter ändern“. Mit `Wall` = 0 mm entsteht eine massive Kuppel. Verknüpfte Felder sind im Maßeditor deaktiviert. Für eine unabhängige Bearbeitung wählen Sie unter „Maßzuweisungen“ den Eintrag „Fester Wert (ohne Ausdruck)“ und wenden die Änderung an. Der aktuelle Wert bleibt erhalten.

Das Materialvolumen wird aus der tatsächlichen Vorschaugeometrie in mm³ berechnet; der Hohlraum wird nicht mitgezählt. Es ist keine Gewichtsangabe. Es wird bei Maßänderungen aktualisiert und bei ungültiger Vorschau ausgeblendet. Beachten Sie beim Ändern der Maße die angezeigte Wandstärkengrenze.

Position X/Y/Z bestimmt den Mittelpunkt der Grundfläche. Bei der Bearbeitung bleibt die vorhandene Drehung erhalten. Innerhalb eines übergeordneten Parts gilt dessen Koordinatensystem. „Abbrechen“ entfernt die Vorschau und stellt die Sichtbarkeit des Originals wieder her.
