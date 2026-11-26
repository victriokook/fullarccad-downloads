# Kunststoffgehäuse: Bearbeitung und Export

Starten Sie FullArcCAD, bevor Sie ein Beispiel öffnen, und speichern Sie eine Arbeitskopie. `Parametric-enclosure.FCStd` zeigt verknüpfte Maße für Befestigungsdome, Durchgangsbohrungen, Dreiecksrippen und Schnapphaken. `Drafted-enclosure.FCStd` ergänzt Entformungsschrägen an den Befestigungsdomen. `Instanced-enclosures.FCStd` verwendet dasselbe Gehäuse in zwei platzierten Komponenten. `Tapered-rib-demo.FCStd` zeigt Entformungsschrägen an Rippen und Befestigungsdomen sowie eine verknüpfte Schnapphakenhöhe.

Setzen Sie im parametrischen Beispiel unter „Parameter ändern“ den Wert `BossHeight` auf 18 mm. Die abhängige Schnapphakenhöhe beträgt danach 20 mm. Rückgängig/Wiederholen stellt beide gemeinsam wieder her. Speichern und erneutes Öffnen erhält Maße und Ausdrücke.

Exportieren Sie STEP/STL über „Verwalten“. Der Export umfasst sichtbare Geometrie: Prüfen Sie die Sichtbarkeit des endgültigen Features, wenn Sie Zwischenstände der Historie betrachten. Unter „Entwurf → Rendern“ können Sie ein isometrisches PNG erzeugen. Im ursprünglich geprüften Ablauf bleiben Kamera, Auswahl, Sichtbarkeit und Historie bei der Bilderzeugung erhalten; der STEP-Reimport stimmt hinsichtlich Materialvolumen und Außenmaßen überein. Öffnen Sie Kunststofffeatures über die Historie. Verknüpfte Felder ändern Sie unter „Parameter ändern“.
