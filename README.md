# FullArcCAD 無料配布版

Windows版・Linux版の試用版ダウンロード専用リポジトリです。
アプリ独自実装のソースは公開しません。外部部品と従来MIT部分のライセンスは維持します。

## ダウンロード

[最新版のダウンロード](https://github.com/victriokook/fullarccad-downloads/releases/latest)
（試用版は [Releases一覧](https://github.com/victriokook/fullarccad-downloads/releases) を参照）

FreeCAD本体は別途必要です。FreeCAD内部のCPython 3.11に対応したビルドです。
WindowsはFreeCAD 1.1.4、LinuxはUbuntu 24.04環境のFreeCAD 1.1.3で確認しました。
未署名の試用版です。全環境・全モデルへの対応を保証するものではありません。

Windows: FullArcCAD-Setup-Freeware-Preview.exe を実行してFreeCADの場所を指定します。
Linux: FullArcCAD-Linux-Freeware-Preview.tar.gz を展開し、FullArcCAD-Linux 内で
`python3 install.py --freecad /実際の場所/FreeCAD.AppImage` を実行します（sudo不要）。

STEPの既定アプリへの変更は、OSの「プログラムから開く」などから利用者が指定してください。
詳細はリリース添付の導入手順と利用条件を確認してください。

既にMITで公開された版の利用・改変・再配布権は変更しません。
FreeCADは同梱せず、SheetMetal等の外部部品は必要なソース・ライセンスを保持しています。
コンパイル済みPython形式は解析を完全に防ぐものではありません。
