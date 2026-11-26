FullArcCAD 非公開 Windows ネイティブ版 ビルドキット

これは完成したEXEではなく、開発PCで2種類のEXEを作成するための非公開ソース一式です。
このZIP自体はソースを含みます。配布・GitHub公開しないでください。

【作成するもの】
outputs/日時/FullArcCAD-Setup-Native-Preview.exe
outputs/日時/FullArcCAD-Portable-Native-Preview.exe

前者はユーザー専用のセットアップ版です。
後者はインストール不要の単一EXEです。初回に内部ファイルをローカルキャッシュへ展開します。
FreeCAD本体はどちらにも同梱していません。FreeCAD内部Python 3.11・64bitが必要です。
「EXEだけでFreeCADも不要」という意味ではありません。

【開発PCに必要なもの】
・Windows 64bit
・Python 3.11 64bit（開発用。利用者には不要）
・Microsoft C++ Build Tools の「C++によるデスクトップ開発」、MSVC x64/x86、Windows SDK
・Windows標準の.NET Framework C#コンパイラー
・初回のPython依存パッケージ取得時はインターネット接続

不足している開発ツールを自動インストールする処理は含めていません。
ビルド時にフォルダ内の仮想環境へCython/setuptools/wheelを取得します。

【使い方】
1. このZIPをすべて、書き込み可能なフォルダに展開します。
2. Build-Windows.cmd をダブルクリックします。
3. 成功すると outputs/日時 に2つのEXEとチェックサム・ビルド記録が作成されます。
4. 失敗時は BUILD-ERROR.txt と画面のエラーを確認します。

FreeCAD起動チェックも行う場合は、PowerShellで次を実行します。
py -3.11 build_native.py --freecad "C:\実際のFreeCADのフォルダ\bin\FreeCAD.exe"
チェックは実際にCAD画面を開き、起動完了マーカーを待ちます。
成功したテスト画面は確認のため開いたままにします。通常操作で終了してください。
起動確認だけではSTEP入出力、保存再読込、板金、CAM等すべての機能を保証しません。

元の開発ソースを直接指定する場合:
py -3.11 build_native.py --source "D:\FluxCAD\test-results\navigation-guard-candidate"
指定しない場合は、今回添付されたZIPのwindows_app/package/runtimeを元にします。
このスナップショットが現在の最新開発版と一致するかは未確認です。

【コード保護の変更】
・本体直下のPythonモジュールと起動処理をCythonでネイティブ.pydへコンパイルします。
・配布物には独自本体の.py/.pyc、生成Cコード、PDBを入れません。
・起動マクロはコンパイル済みモジュールを読み込む最小限の公開可能な処理だけです。
・独自ソースが本体直下へ混入したらビルドを失敗させます。
・FreeCAD、SheetMetal、networkx、SolidWorks readerなど外部部品のソースとライセンスは保持します。
・既にMIT等で公開済みの部分に付与された権利を取り消す処理ではありません。
・ネイティブ化しても逆解析を完全に防ぐことはできません。

【保存先】
セットアップ版は旧版と混ざらないよう、LocalAppData/Programs/FullArcCAD-Nativeに保存します。
旧版のソースやインストールを勝手に削除しません。
ポータブル版の展開キャッシュはLocalAppData/FullArcCADPortable/cacheに作成します。
ポータブル版の設定は単一EXEの隣のFullArcCAD-dataへ保存します。
EXEは書き込み可能なフォルダに置いてください。

【検証状況】
このクラウドのLinux環境では424モジュールのCython変換とPython構文検査が合格しました。
Windows向け.pyd/.exeのコンパイル、FreeCAD内の動作、インストール・アンインストールは未実行です。
Windowsで検証するまで配布しないでください。自動アップロードは一切行いません。
添付元にはtoolsフォルダがなく、一部SolidWorks変換コードが参照する補助スクリプトはありません。
必要な場合は元の開発ソースから補う必要があります。
