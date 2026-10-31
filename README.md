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


## Windows ポータブル版（試作）

インストーラーを使わず、ZIPを展開して起動する形式です。

1. [FullArcCAD-Portable-Windows-Preview.zip](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-freeware-preview1/FullArcCAD-Portable-Windows-Preview.zip) をダウンロードし、書き込み可能なフォルダへすべて展開します。
2. `Start-FullArcCAD.cmd` をダブルクリックします。
3. 初回に、別途用意したFreeCADの `bin/FreeCAD.exe` を選択します。

**FreeCAD本体は同梱していません。** Python 3.11を内蔵したFreeCADが必要です。元の配布版ではWindows版FreeCAD 1.1.4で確認されていますが、このポータブル版のWindows実機起動・CAD操作は未検証です。

FullArcCADのソースコードや、独立したPythonのインストールは不要です。起動用スクリプトは関連付け、ショートカット、インストール登録を行いません。

FreeCADの選択とFullArcCADの状態・設定は展開先の `data` フォルダに保存します。FreeCADを選び直すには `data/freecad-path.txt` を削除して再起動してください。FreeCADや外部部品自体の保存動作をすべて変更したものではありません。

このZIPは公開済み `v0.2.266-freeware-preview1` の本体を再梱包した試作版で、開発中の最新ソースからビルドしたものではありません。利用条件と第三者ライセンスはZIP内に同梱しています。

## お問い合わせ / Contact

質問・ご意見・不具合報告 / Questions, feedback and bug reports:

[victriokook@gmail.com](mailto:victriokook@gmail.com)

不具合の報告には、OS、FreeCADのバージョン、FullArcCADのバージョン、再現手順を添えてください。

For bug reports, please include your OS, FreeCAD version, FullArcCAD version, and steps to reproduce the issue.
