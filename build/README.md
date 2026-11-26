# Native packaging recipes

These scripts document the Windows and Linux native packaging used for the earlier binary previews. FullArcCAD can run directly from source-runtime/FullArcCAD.FCMacro without Cython or a compiler. The source entry point is the verified path for this MIT source publication.

The Windows recipe needs a 64-bit Python 3.11 environment, Cython, setuptools, MSVC and a compatible FreeCAD runtime. It stages project sources, compiles native modules and builds EXE packages. Paths and output folders are relative to the project root except for platform tool discovery.

The Linux recipe records the original Docker SDK and first deb workflow. Its pinned SDK images and hardcoded module counts belong to earlier previews, so it needs adaptation for a different source snapshot. Those locally built Docker images are not hosted in this repository. See linux/deb/README.md for the recorded environment.

Source publication licensing is described in ../LICENSE and ../OPEN-SOURCE.md. Third-party license texts are retained. Previously built binary artifacts may contain earlier project licensing text.
