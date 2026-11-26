# Hollow dome example

Start FullArcCAD before opening `Hollow-dome-demo.FCStd` and save a working copy. Initial dimensions are a 30 × 42 mm base, 12 mm height and 1 mm wall, with an open bottom.

Change `BaseX`, `BaseY`, `DomeRise` and `Wall` in Change Parameters. Set Wall to 0 mm for a solid dome. Linked fields are disabled in the dimension editor. To edit one independently, choose Fixed Value (No Expression) in Dimension Assignments and apply; its current value is retained.

Material volume is measured from the actual preview shape in mm³, excluding the hollow cavity. It is not weight. It updates with dimensions and disappears for invalid previews. Use the displayed wall limit when adjusting dimensions.

Position X/Y/Z places the base center; editing preserves the existing rotation. Position inside a parent Part uses its coordinate system. Cancel removes the preview and restores source visibility.
