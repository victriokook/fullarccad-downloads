# FullArcCAD


FreeCADにFusion 360風の操作画面を加える拡張機能です。
このリポジトリは配布ファイルと案内の公開用です。独自実装のソースは公開しません。


## Windows版 — 0.2.266 Native Preview 1


- [インストーラーEXE](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-native-preview1/FullArcCAD-Setup-Native-Preview.exe)
- [インストール不要のポータブルEXE](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-native-preview1/FullArcCAD-Portable-Native-Preview.exe)
- [導入手順・検証範囲・SHA256・利用条件](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.266-native-preview1)


**FreeCAD本体は別途必要です。内蔵Python 3.11・64bitに対応し、FreeCAD 1.1.4で確認しました。**
ポータブル版は初回に内部ファイルをローカルキャッシュへ展開し、EXE隣の `FullArcCAD-data` に設定・作業データを保存します。書き込み可能なフォルダーに置いてください。


本体422＋起動処理2の424モジュールをネイティブ拡張へコンパイルしています。独自実装のPythonソース・バイトコード、生成C、デバッグ情報を配布物へ同梱していないことを検査しました。汎用の起動・Qt接続処理のみテキスト形式です。


起動、STEP入出力、FCStd保存・別プロセス再読込、寸法編集、Undo/Redo、インストール・アンインストール、Native版未インストールでのポータブル起動を検証しました。未署名の開発版で、別PC・全機能の網羅検証は未実施です。高度なSolidWorks BRep変換の追加コンバーター・補助ツールは含みません。


## Linux版 — 0.2.266 Native Preview 1

- [Linux x86_64 ネイティブ版アーカイブ](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-native-preview1/FullArcCAD-Linux-Native-Preview-x86_64.tar.gz)
- [Linux導入手順](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-native-preview1/README-Linux-ja.md)
- [検証範囲・SHA256・利用条件](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.266-native-preview1)

FreeCAD本体は別途必要です。展開したFreeCAD AppImageのAppRunと内蔵CPython 3.11・64bitを使用します。Ubuntu 24.04 x86_64のDocker／Xvfb上でFreeCAD 1.1.3・Python 3.11.14・Qt 6.8.3を検証しました。

本体424＋Linux導入・削除・起動3の427モジュールをネイティブ化し、独自ソース・バイトコード・生成C/C++・デバッグ情報の非同梱を検査しました。STEP入出力、保存・別プロセス再読込、寸法編集、Undo/Redo、導入・削除、削除後のポータブル起動が合格しています。実デスクトップ・Wayland・他ディストリビューション・ARM64・全機能は未検証です。

## ライセンス・お問い合わせ


FreeCAD本体は同梱していません。SheetMetal、NetworkX、SolidWorks reader等の外部部品の必要なソースとライセンス、および従来MIT部分の表示を保持します。既にMIT等で付与された権利を取り消すものではありません。ネイティブ化は完全な逆解析防止を保証しません。


質問・ご意見・不具合報告: [victriokook@gmail.com](mailto:victriokook@gmail.com)


不具合報告には、OS、FreeCAD版、FullArcCAD版、再現手順を添えてください。
For bug reports, please include your OS, FreeCAD version, FullArcCAD version, and steps to reproduce the issue.

