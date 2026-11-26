# Current licensing

FullArcCAD project-managed code and assets are now MIT licensed. See [OPEN-SOURCE.md](OPEN-SOURCE.md) and [LICENSE](LICENSE). The following text is the historical 2026-11-02 review record. Earlier reserved-rights and no-relicensing statements for project-managed material are superseded by the 2026-11-26 MIT grant. Third-party licenses remain applicable.

# Licenses, origins and external runtime / ライセンス・出所・外部ランタイム

This is a dependency-reduced FullArcCAD preview. SheetMetal/NetworkX and their execution paths are excluded; upstream sheet metal features are unavailable. A separate independent rectangular/sequential-bend prototype is described in INDEPENDENT-SHEETMETAL.md.

## Historical project material

The historical FluxCAD/FullArcCAD MIT notice is reproduced in `LEGACY_MIT_LICENSE.txt`. Existing MIT permissions remain intact for covered material, including covered portions of changed files. Reserved-rights language applies only to independently owned additions not otherwise licensed. Compiling Python code does not change any underlying license.

The maintainer states that project-managed code, SVG icons, templates and examples were primarily created through the development chat, and that known external code is listed in the notices. A local file inventory and historical comparison were retained privately. The local 0.2.242 MIT-labelled source archive matched its historical SHA-256 record; 350 pre-documentation-update files matched it, 135 had changed at the same path, and 119 were absent. This is a local historical comparison and maintainer declaration, not proof of independent authorship or a legal clearance opinion.

## Bundled third-party reader

- Component: XRTC5/sldprt-export reader subset.
- Upstream: https://github.com/XRTC5/sldprt-export
- Pinned commit: `ebde7524b3876c5d78c7e2248f2eba9b5725a6c0`.
- License/source records: `solidworks_reader/LICENSE` and `solidworks_reader/SOURCE.json`.
- LICENSE and all five bundled Python source files match pinned upstream SHA-256 values; original MIT notice is retained. No upstream reader code is relabeled proprietary.
- The upstream reader cites cadmpeg format documentation (CC BY 4.0). Those credits remain in its source comments. This package does not bundle the cadmpeg decoder or documentation.

## FreeCAD and external libraries

FreeCAD is not bundled or downloaded by the Windows package. Linux prompts the user to select an official py311 AppImage already available to them and prepares that separate runtime. The FreeCAD installation and its dependencies retain their own licenses. FullArcCAD uses FreeCAD public Python/GUI APIs and runs inside that process.

- Project and source: https://github.com/FreeCAD/FreeCAD
- FreeCAD 1.1.4 Windows source version used in validation: `4fd3bf320d9566a27e60069fc8387448aaa3a094`.
- FreeCAD 1.1.3 Linux runtime source/download: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3
- Official license explanation: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/License.md
- The accompanying `FREECAD-LICENSE.html` is the unmodified license document from the tested Windows runtime. Some separately supplied modules identify LGPL-2.1-or-later; `LGPL-2.1.txt` is included without alteration. Read the selected runtime's own license and third-party notices for exact terms, including Qt/PySide, OpenCASCADE, Python, NumPy, fontTools and Coin/pivy. These components are not all under one identical license.

### Selecting a replacement runtime

Windows: the optional environment variable `FULLARCCAD_ENGINE` takes precedence and can point to a compatible FreeCAD.exe for both installed and portable editions. An invalid explicit path is rejected rather than silently ignored. For the installed edition, `launcher.json` next to `FullArcCAD.exe` contains the `engine` path; select an existing compatible FreeCAD.exe. The portable launcher also reads the selected engine from its configuration. Keep models backed up and close the app before changing this setting. Linux: `fullarccad --configure --freecad /path/to/compatible/AppRun` or select a compatible official py311 AppImage on first run. ABI compatibility is required: 64-bit CPython 3.11 for this preview. No application term prohibits a compatible user-modified FreeCAD runtime; technical compatibility is not guaranteed for arbitrary versions.

## Assets and examples

Project-managed vectors live in `icons/` and `templates/`. Local user fonts are selected at runtime and are not bundled. The eight example FCStd documents have `All rights reserved` License metadata; that does not establish ownership or cancel any existing permission. No new relicensing is made here. Screenshots showing external models/textures require their own attribution; an application's runtime license does not cover those models.

## Review scope

A local exact-AST-body comparison checked 1,534 installed FreeCAD Mod Python files against 1,731 substantial application functions, and exact SVG bytes were compared. No exact matches were found. This limited mechanical check does not cover renamed code, algorithmic similarity, other repositories, training data, patents, trademarks or every legal issue. No statement in this package is an attorney's clearance or a guarantee that all third-party rights have been resolved.

日本語: 既知の同梱外部コードの原文表示、過去MIT部分の権利、FreeCADの別途利用と変更版選択、使用例メタデータの説明を整理しました。これは確認した構成についての技術・文書対応であり、「すべてのライセンス問題が法的に解消した」と認証するものではありません。
