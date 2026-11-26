# Open-source publication update — 2026-11-26

Project-managed code and assets, including examples, are MIT licensed under LICENSE and OPEN-SOURCE.md. This explicit grant supersedes the historical example-metadata/no-relicensing statements below for project-managed examples. Original third-party notices and licenses are retained.

# Third-party software / 第三者ソフトウェア

The MIT license in this repository applies to FluxCAD's original code and assets. It does not change the license of FreeCAD, its code, its artwork or its dependencies.

## FreeCAD

FluxCAD runs inside a separately installed FreeCAD. It uses the public Python/GUI interfaces, native modeling objects, Sketcher, Part, TechDraw and modules such as FreeCAD's bundled BOPTools. Native command icons are loaded from the installed FreeCAD resource system at runtime.

- Project and source: https://github.com/FreeCAD/FreeCAD
- Licensing information: https://www.freecad.org/contributing.php?lang=eng
- License: GNU Lesser General Public License (LGPL), as specified by the FreeCAD version being used.

This package does not redistribute FreeCAD binaries, Python, OpenCASCADE, Qt/PySide, Coin/pivy or copies of FreeCAD's native icon resources. They come from the user's FreeCAD installation and retain their respective licenses and notices. If a distributor later bundles a FreeCAD runtime, they must separately retain and satisfy its applicable license and source-distribution requirements; this document is not a substitute for those notices.

## FluxCAD assets

The project-maintained vector assets are under `icons/` and `templates/`; example documents and guides are under `examples/`. Historical MIT notices and applicable third-party permissions remain in effect. A file-level local provenance inventory is retained with the 2026-11-02 follow-up evidence; it is not independent proof of authorship. Screenshots may show FreeCAD native interface resources, and each published screenshot must retain any model/texture attribution required for it.

FreeCAD, Autodesk and Fusion are names of their respective projects or owners. Naming them describes the runtime dependency and workflow inspiration; no affiliation or endorsement is claimed.

日本語: FluxCADのMITライセンスはFreeCADや依存ライブラリへ適用されるものではありません。FreeCAD本体は同梱していません。将来ポータブル版などを同梱する場合は、その版に含まれるライセンス・表示・ソース提供条件を別途確認してください。


## Dependencies in this dependency-reduced release

- sldprt-export parser: MIT; exact commit and source hashes in solidworks_reader/SOURCE.json; original LICENSE and headers retained. https://github.com/XRTC5/sldprt-export . Parser documentation includes attributed cadmpeg format references.
- cadmpeg v0.6.1 is NOT bundled in this Native Preview. The optional advanced SolidWorks BRep conversion path also needs development-tree helper scripts that are not included. That conversion path is not supported or validated by this package. Upstream: https://github.com/cadmpeg/cadmpeg/tree/v0.6.1 (Apache-2.0 code; CC-BY-4.0 documentation).

The eight FCStd examples examined in the 2026-11-02 release have License metadata set to `All rights reserved`. Earlier references to MIT metadata on publication copies do not describe this payload. Metadata alone does not establish authorship or revoke any previously granted permissions. Example provenance and applicable historical permissions remain subject to review; no relicensing is made here. Third-party code/resources retain their own licenses.

SheetMetal and its bundled NetworkX dependency are excluded from this release. Upstream SheetMetal commands and kernels remain unavailable. The independent rectangular/sequential-bend prototype uses original analytic Part geometry and does not call that addon. The separately installed FreeCAD runtime retains its original licenses.

## External runtime review (2026-11-02)

Direct calls also use FreeCAD CAM/Path, Sketcher ProfileLib, Draft, NumPy, fontTools and Qt/PySide/pivy supplied by the separate FreeCAD installation. Inspected Python modules and installed package metadata retain their individual license terms; a single FreeCAD-wide label is not a substitute for the full runtime notices. FreeCAD and those runtime libraries are not redistributed in this FullArcCAD package. Local fonts are selected by the user; font files are not bundled here. Full provenance and transitive dependency licensing review remain incomplete.
