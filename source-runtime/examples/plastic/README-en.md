# Plastic case: editing through export

Start FullArcCAD before opening an example, then save a working copy. `Parametric-enclosure.FCStd` demonstrates linked boss, through-hole, gusset and snap dimensions. `Drafted-enclosure.FCStd` adds boss draft; `Instanced-enclosures.FCStd` shares a case between two placed components; `Tapered-rib-demo.FCStd` demonstrates rib/boss draft and linked snap height.

In Change Parameters, set BossHeight to 18 mm in the parametric example. The dependent snap height becomes 20 mm. Undo/Redo restores both together. Save and reopen to retain dimensions and expressions.

Use Manage to export STEP/STL; export includes visible geometry, so check final-feature visibility when inspecting historical features. Use Design → Rendering for an isometric PNG. The verified workflow preserves camera, selection, visibility and history during image generation. STEP reimport matches the edited material volume and bounds. Edit plastic features from the history; linked fields are adjusted through Change Parameters.
