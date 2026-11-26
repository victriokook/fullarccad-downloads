# FullArcCAD

**FullArcCAD is now open source under the MIT License.** Development of this release is complete, and its source is available for anyone to use, study, modify, redistribute and use commercially under the license terms.

FullArcCAD is a FreeCAD add-on that brings a Fusion 360–style modeling workflow to FreeCAD. It includes a ribbon interface, sketches, solid modeling, surfaces, meshes, drawing tools and an independent sheet metal implementation.

**開発完了に伴い、FullArcCADのソースをMITライセンスで公開しました。** 利用・改変・再配布・商用利用ができます。FreeCADの拡張機能として、Fusion 360風の操作環境を提供します。

## Run from source

1. Install a compatible 64-bit FreeCAD separately. The current source entry point targets embedded Python 3.11.
2. Download this repository as a ZIP and extract it, or clone it with Git.
3. In FreeCAD, open **Macro → Macros**, set the macro directory to **source-runtime**, then run **FullArcCAD.FCMacro**.
4. Choose **Settings → Language** and restart to change the UI language.

Windows example, from the repository directory in PowerShell:

```powershell
& 'C:\Program Files\FreeCAD 1.1\bin\FreeCAD.exe' "$PWD\source-runtime\FullArcCAD.FCMacro"
```

Linux example, with a compatible extracted FreeCAD AppImage:

```sh
/path/to/squashfs-root/AppRun "$PWD/source-runtime/FullArcCAD.FCMacro"
```

日本語 — FreeCADの「マクロ → マクロ」でsource-runtimeフォルダーを選び、FullArcCAD.FCMacroを実行します。ソース起動にネイティブコンパイルは不要です。

## Downloads and scope

- [Windows installer / portable EXE and Linux DEB / TAR](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.307-native.mirror-combine.preview1)
- [English introduction video](https://youtu.be/rxC4_jMuJPE)
- [Source code](source-runtime) and [native packaging recipes](build)

This publication contains the current project source, including independent sheet metal preview 41 and the mirrored-body Combine fix. The downloadable binaries predate this MIT publication and may contain earlier licensing text for project-managed additions. The explicit MIT grant here applies to the project-managed material published in this source release. Third-party components retain their own licenses.

## License

See [LICENSE](LICENSE), [licensing scope](OPEN-SOURCE.md), and [third-party notices](source-runtime/THIRD_PARTY_NOTICES.md). The bundled MIT reader retains its original notice. FreeCAD and its runtime dependencies are installed separately under their own licenses. The project-maintained code, build scripts, icons, templates, examples and guides are covered by the MIT grant. Legacy FluxCAD copyright notices are retained.

The source is provided as-is under the MIT License. For the supported sheet metal inputs and limitations, see [INDEPENDENT-SHEETMETAL.md](source-runtime/INDEPENDENT-SHEETMETAL.md).

Questions and bug reports are welcome in GitHub Issues. Public contact: victriokook@gmail.com.
