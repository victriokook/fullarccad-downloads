# Contributing

FullArcCAD is MIT licensed. Report issues and submit focused pull requests on GitHub. Include the FreeCAD version, operating system, reproduction steps and expected result. Use a small model you can share publicly.

Run source-runtime/FullArcCAD.FCMacro inside FreeCAD to start from source. Preserve selection, Undo/Redo, parameter dependencies and saved-document reopening when changing modeling behavior. Test in a separate FreeCAD profile with copies of models.

Keep UI strings in i18n.tr() and retain third-party notices. Build recipes for optional native distributions live in build/. The source macro runs without Cython or a native compiler.
