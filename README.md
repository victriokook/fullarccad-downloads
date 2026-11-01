# FullArcCAD

## SheetMetal依存を除いた修正版を公開しました — 2026年11月2日

**この版では板金機能を利用できません。** 通常のCAD機能・STEP入出力・10言語の検証を行ったWindows／Linuxプレビューです。

[修正版の説明・全ダウンロード](https://github.com/victriokook/fullarccad-downloads/releases/tag/v0.2.266-license-mitigation-preview1)

- [Windows ポータブルEXE](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview1/FullArcCAD-License-Mitigation-Portable.exe)
- [Windows インストーラーEXE](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview1/FullArcCAD-License-Mitigation-Setup.exe)
- [Ubuntu 24.04 amd64用deb](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview1/fullarccad_0.2.266%2Blicensefix.preview1-1_amd64.deb)
- [Linux tar.gz](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview1/FullArcCAD-License-Mitigation-Linux-amd64.tar.gz)
- [SHA-256一覧](https://github.com/victriokook/fullarccad-downloads/releases/download/v0.2.266-license-mitigation-preview1/SHA256SUMS.txt)

## 配布再開：SheetMetal依存を除外した修正版（2026年11月2日）

一時停止していた配布を、構成を変更したプレビュー版として再開します。この版ではSheetMetal本体・リソース・付属NetworkXを同梱せず、起動時の読み込みと板金カーネルの呼び出しを除去しました。

**板金機能は利用できません。** ベース板、フランジ、展開、ヘム、輪郭フランジ、折曲げ、コーナーリリーフ、継ぎ目の操作は非表示です。板金機能を使う既存データの再計算・編集には対応しません。元データを保全し、コピーで試してください。

通常のスケッチ・ソリッド操作、寸法編集、保存・再読込、STEP入出力は検証済みです。日本語、英語、ドイツ語、繁体字中国語、スペイン語、フランス語、簡体字中国語、韓国語、イタリア語、ブラジルポルトガル語の10言語に対応します。

### ダウンロードと導入

- Windows: `FullArcCAD-License-Mitigation-Portable.exe`（インストール不要）または `FullArcCAD-License-Mitigation-Setup.exe`。
- WindowsではCPython 3.11を内蔵したFreeCADを別途用意してください。FreeCAD 1.1.4で検証しています。
- Ubuntu 24.04 amd64: `sudo apt install ./fullarccad_0.2.266+licensefix.preview1-1_amd64.deb`。
- Linuxの初回起動では、[公式FreeCAD 1.1.3 Linux x86_64 py311 AppImage](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3)を選択します。FUSE不要で自動展開します。`README-Linux-ja.md`に詳細があります。
- Linux手動導入用のtar.gzも添付しています。FreeCAD本体はどの配布物にも同梱していません。
- 整合性の確認には `SHA256SUMS.txt`、検証概要には `VALIDATION-SUMMARY.json` を参照してください。

### 確認した範囲

Windowsの全432ネイティブモジュール、10言語、設定保存後の再起動、スケッチ・寸法編集・Undo/Redo、STEP入出力、別プロセスでのFCStd再読込と再編集、最終ポータブルEXEからのモデル読み込み、配布内容の監査がPASSです。Windowsインストーラーの実インストールは未検証です。

LinuxはクリーンなUbuntu 24.04 amd64コンテナー・Xvfb上で、一般ユーザーによる初回設定、FreeCAD AppImage自動展開、10言語、CAD操作、更新、削除・purge時のユーザーデータ保持など27項目がPASSです。実デスクトップ・Wayland・他のディストリビューションは未検証です。

### ライセンスについての説明

「SheetMetalは一律GPL」「ソースを保持するだけで十分」といった以前の説明は正確ではありませんでした。確認した同梱LICENSEと主要ファイルヘッダーはLGPL表記でした。今回は部品名だけで法的適合を断定せず、SheetMetal依存を除いた配布構成に変更しました。

これは依存除去と技術検証の報告であり、法的適合全般の保証・認証ではありません。残るFreeCADや第三者ソフトウェアには各ライセンスが適用されます。既存MIT部分の権利と第三者ライセンス上の権利を変更・取り消すものではありません。`LEGACY_MIT_LICENSE.txt`、`THIRD_PARTY_NOTICES.txt`、`TERMS-ja.txt`を参照してください。

過去の配布物は引き続き取り下げ状態です。新規利用には、このリリースのファイルを使用してください。

## English

Downloads resume with a dependency-reduced preview. SheetMetal, its resources and bundled NetworkX are excluded. Startup loading and sheet metal kernel calls have been removed. **Sheet metal features are unavailable**, including base plates, flanges, unfolding, hems, contour flanges, folding, reliefs and seam gaps. Recomputing or editing existing sheet metal features is unsupported; preserve original documents and work on copies.

Normal sketch/solid workflows, dimension editing, save/reopen and STEP import/export were validated. Ten interface languages remain available. FreeCAD is a separate prerequisite, not bundled: Windows was tested with FreeCAD 1.1.4 / CPython 3.11; Linux with the official FreeCAD 1.1.3 x86_64 py311 AppImage.

Windows: choose the portable EXE or setup EXE. Linux: install the amd64 deb on Ubuntu 24.04, then select the official py311 AppImage on first launch. See `README-Linux-en.md` for setup. A tar.gz is available for manual use.

Windows validation covered 432 native modules, all ten languages, restart persistence, sketches, dimension undo/redo, STEP roundtrips, separate-process document reopen/reedit, final portable launch and package audits. Actual Windows installer installation was not tested. Linux passed 27 install/runtime/update/removal checks in a clean Ubuntu 24.04 amd64 container with Xvfb and an unprivileged GUI user. Real desktop/Wayland and other distributions were not tested.

Earlier blanket statements about GPL and keeping source files were inaccurate. The bundled LICENSE and key headers inspected were LGPL notices. This release removes the dependency; it is not a certification of overall legal compliance. Existing MIT permissions and third-party license rights remain intact. Consult the attached notices, terms, validation summary and SHA-256 checksums. Old executable packages remain withdrawn.
