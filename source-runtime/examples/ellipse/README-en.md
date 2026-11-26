# Editing the numeric ellipse example

Start FullArcCAD before opening `Positioned-ellipses-demo.FCStd`, then save a working copy. The example contains two 40 × 20 mm ellipses extruded 8 mm, initially centered at X −35/+35 mm and Y 10 mm.

In Change Parameters, changing `Gap` from 70 to 100 mm moves the centers to −50/+50 mm. `Width`, `Height` and `CenterY` control both ellipses. Width and height are full lengths.

To edit only the left ellipse, set its `EllipseCenterX` and `EllipseWidth` assignments to **Fixed Value (No Expression)** and apply. This keeps their current values. Enter sketch editing, use **Move Ellipse Center** to set left X to −50 mm, then **Resize Ellipse** to set its width to 50 mm. Leave the linked Y and height unchanged. Existing extrusions update; the right ellipse retains its width. Later Gap edits affect only the still-linked right center.

Linked fields are disabled. Remove both coordinate bindings to enable Set to Origin. Coordinates are local to the sketch. Recreate an ellipse to swap major/minor axes or use equal dimensions. Independent edits, Undo/Redo and save/reload were verified on a copy; shipped originals remain unchanged.




With multiple ellipses, select one supported outline in sketch editing before opening an editor to initialize that target. Construction axes and ordinary ellipses do not count as numeric ellipse selection. Multiple supported outlines fall back to the first list item.
