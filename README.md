# FullArcCAD

## 結合修正版 — Windows x64・Linux amd64

- [Windowsインストーラー](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.307-native.mirror-combine.preview1/FullArcCAD-Setup-Native-Preview.exe) / [Windowsポータブル版](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.307-native.mirror-combine.preview1/FullArcCAD-Portable-Native-Preview.exe)
- [Ubuntu 24.04 amd64用deb](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.307-native.mirror-combine.preview1/fullarccad_0.2.307%2Bindependent.sheet.preview41.combinefix1-1_amd64.deb) / [Linux tar.gz](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.307-native.mirror-combine.preview1/FullArcCAD-Mirror-Combine-Fix-Linux-amd64.tar.gz)
- [導入手順・検証結果・SHA-256](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.307-native.mirror-combine.preview1)

元のボディと、そのボディを参照するミラーから作った別ボディを結合できます。独自板金プレビュー41をベースにしています。

## 独自板金プレビュー5 — Windows x64

独自実装の板金機能を追加したWindows向け試用版です。**以前の「板金機能なし」のライセンス文書整備版とは別の新しいプレビュー**です。旧SheetMetalアドオン・付属NetworkXは引き続き同梱しません。

### ダウンロード

- **推奨:** [サンプル・ガイド付きWindows ZIP](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/FullArcCAD-SheetMetal-Preview5-Windows-x64.zip)を解凍し、`Start-SheetMetal-Preview5.cmd`を実行。
- [ポータブルEXE単体](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/FullArcCAD-SheetMetal-Preview5-Portable.exe)も添付。
- FreeCAD本体は別途必要です。**FreeCAD 1.1.4 / CPython 3.11 x64で検証**しています。互換ランタイムを選択してください。ZIPのCMDは検証済みソフトウェアOpenGLを使用します。
- [操作ガイド](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/SheetMetal-guide-ja-en.md)、[検証概要](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/VALIDATION-SUMMARY.json)、[SHA-256](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/SHA256SUMS.txt)。

### 追加した機能

- 矩形ベースと4辺からの曲げ位置選択、最大8回の連続曲げ。
- 独立した1～4側面のフランジ。各面の半径・正負角度・直線長・K係数を個別指定。
- ベースの貫通丸穴を最大32個。既存の曲げ・トレイ・展開への一括反映、Undo/Redoと保存後の再編集。
- 切り欠き付きの実外形展開、外形/曲げ線/穴CIRCLEを分けたDXF、形成・展開STEP、曲げ表CSV。

![穴付き板金トレイ](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.271-independent-sheet-preview5/Preview-tray.png)

### 検証・制限

形状・互換性・回帰・実GUIなど**146項目がPASS**。別のDXFリーダーで32本の線と4つの円を読み込み、円中心と半径を確認。STEPの体積と穴のワイヤー、最終ポータブル起動、434ネイティブモジュールの配布監査も通過しています。ローカルQwen2.5-Coderを設計レビューに使用し、形状と操作は独立して検証しました。製品利用時にAIは不要です。

対象は矩形・一定板厚です。角は開いたままで、曲げ部/壁面の穴、長穴、ヘム、任意輪郭、トレイ壁への追加連続曲げは未対応です。K係数は実材料・工具で校正してください。工具進入・曲げ順序・加工精度の認証ではありません。新しい文書はこの版で編集してください。旧版は新形式の再計算を拒否します。

**今回はWindowsポータブルのみ。Linux板金版と新インストーラーの実導入は未検証です。** 既存のLinux版は引き続き板金なしです。新規画面は日本語/英語対応で、従来10言語すべてでの新画面検証は行っていません。

同梱の既存MIT許諾・第三者通知を保持しています。技術的な依存除去と独自実装の追加であり、包括的な法的適合認証を示すものではありません。

## English

Windows-only independent sheet-metal preview: rectangular bases, four starting sides, up to eight sequential full-width bends, one to four independent tray walls, up to 32 base through holes, true flat-outline/DXF circles, STEP and bend CSV. Download the ZIP for the launcher, sample, guide and license notices. A separate FreeCAD CPython 3.11 x64 runtime is required; tested with FreeCAD 1.1.4. 146 checks, final portable launch and the 434-module distribution audit passed. Corners remain open; arbitrary outlines, hems, wall/bend holes and tooling/manufacturing certification are outside scope. Linux sheet functionality is not released here. This does not restore the excluded upstream SheetMetal addon. Preserve prior MIT permissions and third-party notices; technical validation is not comprehensive legal clearance.


---

## 旧ライセンス文書整備版（第2版・板金なし） — 2026年11月2日

**板金機能は利用できません。** 確認した技術・表示面の指摘へ対応しましたが、包括的な法的認証ではありません。

[説明と全ダウンロード](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.266-license-mitigation-preview2)

- [Windows ポータブル](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview2/FullArcCAD-License-v2-Portable.exe)
- [Windows インストーラー](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview2/FullArcCAD-License-v2-Setup.exe)
- [Ubuntu 24.04 amd64 deb](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview2/fullarccad_0.2.266%2Blicensefix.preview2-1_amd64.deb)
- [Linux tar.gz](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview2/FullArcCAD-License-Docs-v2-Linux-amd64.tar.gz)
- [ライセンス・出所・ランタイム選択](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview2/LICENSES-AND-SOURCES.md)

## ライセンス文書・ランタイム選択を整備した第2版 — 2026年11月2日

確認した技術・表示面の指摘を修正したプレビューです。**「すべてのライセンス問題が法的に解消した」と認証するものではありません。** 板金機能は引き続き利用できません。

### 修正内容

- FreeCADの原文ライセンス文書、LGPL 2.1本文、既存MIT本文、外部リーダーの原文MIT表示を同梱しました。
- 出所・適用範囲・上流ソースと互換ランタイムの選択方法を `LICENSES-AND-SOURCES.md` にまとめました。
- 利用条件で、第三者ライセンスによる利用・変更・必要なデバッグ解析等の権利を制限しないことを明記しました。
- Windowsは環境変数 `FULLARCCAD_ENGINE` で互換FreeCAD.exeを明示指定できます。既存設定より優先されます。Linuxは既存の `fullarccad --configure --freecad ...` を使用できます。CPython 3.11・64bitのABI互換性が必要です。
- 使用例のライセンスメタデータに関する古い説明を配布物の内部文書でも訂正しました。使用例を勝手に再ライセンスしていません。過去のMIT許諾は維持されます。
- SheetMetal本体・付属NetworkX・板金カーネルの呼び出しは除外済みです。

### 導入

Windowsは `FullArcCAD-License-v2-Portable.exe` または `FullArcCAD-License-v2-Setup.exe` を使用してください。FreeCAD 1.1.4 / CPython 3.11で検証しています。

Ubuntu 24.04 amd64は `sudo apt install ./fullarccad_0.2.266+licensefix.preview2-1_amd64.deb`。初回に公式FreeCAD 1.1.3 x86_64 py311 AppImageを選択します。FreeCAD本体はこの配布物に同梱していません。

### 検証と確認範囲

Windows新版は実導入・同梱文書・ランタイム明示指定・起動・再導入・削除など17項目、最終ポータブル起動、配布内容監査がPASSです。Linux新版はクリーンUbuntuでの導入、ライセンス文書の導入先配置、版番号、削除と配布内容監査がPASSです。

本体432 Windows / 435 Linuxネイティブモジュールは前版の監査済みバイナリと一致します。前版での全10言語・スケッチ・STEP入出力・保存再読込等の検証を引き継ぎます。今回はランチャーと文書・パッケージを変更し、変更箇所を検証しました。Linux実デスクトップ・Waylandは未検証です。

既知の同梱外部リーダー6ファイルは固定上流コミットと一致し、MIT表示を保持しています。作成経緯の申告と過去のMIT表記付き配布アーカイブも記録しました。FreeCAD側1,534 Pythonファイルおよび除外済みSheetMetal 33 Pythonファイルと、本体の一定以上の長さの関数を機械比較し、構文木の一致は見つかりませんでした。SVGのバイト一致もありませんでした。これは独立した権利確認や流用がないことの証明ではありません。全第三者権利・LGPLの最終的な法的評価・特許や商標等の確認を保証するものではありません。

原文通知・利用条件・出所一覧・検証JSONとSHA-256一覧を添付しています。法的な最終判断が必要な場合は、実装・配布構成とこれらの証拠をもとに権利者や専門家の確認が必要です。

## English

This second preview remediates identified technical/documentation findings; it is **not comprehensive legal clearance**. Sheet metal features remain unavailable. The package now includes unmodified FreeCAD/LGPL texts, legacy and reader MIT notices, an origin/source/license index, explicit preservation of third-party modification and required debugging rights, corrected example-metadata documentation, and Windows `FULLARCCAD_ENGINE` selection for a compatible FreeCAD.exe.

Windows actual installation, documents, explicit runtime selection, launch, reinstall/removal and data preservation passed 17 checks; the final portable and package audit passed. Linux clean installation, license-document placement, version/removal and package audit passed. The 432 Windows / 435 Linux native modules are identical to previously audited binaries, retaining prior ten-language/CAD/STEP/save/reopen evidence. Only launchers, documentation and packaging changed. A real Linux desktop/Wayland remains untested.

The pinned MIT reader files and notices were verified. Maintainer origin declarations and the local historical MIT archive comparison were recorded. Exact substantial AST-body and SVG-byte comparisons against installed FreeCAD and the excluded addon found no matches; that limited check is not proof of originality or freedom from all third-party rights. No claim of final legal clearance for every dependency, copyright, patent or trademark is made. See attached notices, terms, source index, validation records and checksums.
