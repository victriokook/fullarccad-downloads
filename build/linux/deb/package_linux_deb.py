from pathlib import Path
import json,shutil,subprocess,hashlib,tarfile,gzip,os
r=Path('/work');stage=r/'stage';runtime=stage/'runtime';out=r/'output';out.mkdir(exist_ok=True)
version='0.2.266+licensefix.preview2-1'
assert len(list(runtime.glob('*.so')))==432
(stage/'VALIDATION.json').unlink(missing_ok=True)  # Old preview's report is not evidence for this build.
for binary in stage.rglob('*.so'):
 path=subprocess.check_output(['patchelf','--print-rpath',str(binary)],text=True).strip()
 if path:subprocess.run(['patchelf','--remove-rpath',str(binary)],check=True)
# Keep the bundled third-party helper usable on systems without /usr/bin/python.
helper=runtime/'addons/SheetMetal/tools/calc-unfold.py'
if helper.is_file():helper.write_text(helper.read_text(encoding='utf-8').replace('#!/usr/bin/python\n','#!/usr/bin/python3\n'),encoding='utf-8')
shutil.copy2(r/'linux_deb_bootstrap.py',stage/'bootstrap.py')
guide='''FullArcCAD Linux native preview — 10 languages
Sheet metal features are unavailable; SheetMetal is excluded.

Ubuntu 24.04 x86_64 is the tested target. FreeCAD is not bundled.
Install: sudo apt install ./fullarccad_0.2.266+licensefix.preview2-1_amd64.deb
Then launch FullArcCAD from the application menu.
On first launch choose the official FreeCAD Linux x86_64 py311 AppImage.
It is extracted automatically without FUSE or root access.
Compatible download: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3

Optional terminal setup:
fullarccad --configure --freecad /path/to/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage
fullarccad --engine-info

Use Settings > Language and restart to switch languages.
Remove: sudo apt remove fullarccad
User models, settings and engine caches are retained when removing the package.
Settings: ~/.config/fullarccad-native
State: ~/.local/state/fullarccad-native
Engine cache: ~/.cache/fullarccad-native/engines
XDG_CONFIG_HOME/XDG_STATE_HOME/XDG_CACHE_HOME override these locations.
No per-user files are created by package installation scripts.

The tar.gz is also available for portable/manual use; its install/uninstall
helpers are not needed for the deb package.
'''
ja='''FullArcCAD Linuxネイティブ・10言語プレビュー
この版ではSheetMetalを除外しており、板金機能は利用できません。

検証対象はUbuntu 24.04・x86_64です。FreeCADは別途必要です。
debは「sudo apt install ./fullarccad_0.2.266+licensefix.preview2-1_amd64.deb」で導入できます。
アプリケーションメニューのFullArcCADから起動してください。
初回は公式FreeCADのLinux x86_64 py311 AppImageを選択すると自動展開します。
FUSEの導入や手動展開、管理者権限は不要です。
対応ダウンロード先: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3

端末で設定する場合:
fullarccad --configure --freecad /path/to/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage
fullarccad --engine-info

設定メニューの言語を選択して再起動すると反映されます。
削除は「sudo apt remove fullarccad」。モデルやユーザー設定、エンジンキャッシュは削除しません。
設定は~/.config/fullarccad-native、実行状態は~/.local/state/fullarccad-native、
エンジンキャッシュは~/.cache/fullarccad-native/enginesです。XDG変数にも対応します。
debのインストール時にはホーム内の設定を作成しません。
tar.gz版はポータブル・手動導入向けとして残しています。
'''
(stage/'README-en.md').write_text(guide,encoding='utf-8');(stage/'README-ja.md').write_text(ja,encoding='utf-8')
root=r/'deb-root';root.mkdir(exist_ok=True);lib=root/'usr/lib/fullarccad'
(lib/'VALIDATION.json').unlink(missing_ok=True)
shutil.copytree(stage,lib,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for p in lib.rglob('*'):
 if p.is_file() and p.name in ('.gitattributes','.gitignore','.gitmodules'):p.unlink()
for name in ('install','uninstall'):
 (lib/name).unlink(missing_ok=True)
 for p in lib.glob('_fullarc_linux_'+name+'.*.so'):p.unlink()
bindir=root/'usr/bin';bindir.mkdir(parents=True,exist_ok=True)
(bindir/'fullarccad').write_text('#!/bin/sh\nexec /usr/bin/python3 /usr/lib/fullarccad/bootstrap.py fullarccad "$@"\n',encoding='utf-8')
desktop=root/'usr/share/applications';desktop.mkdir(parents=True,exist_ok=True)
(desktop/'org.fullarccad.FullArcCAD.desktop').write_text('''[Desktop Entry]
Type=Application
Name=FullArcCAD
Comment=Parametric 3D CAD workspace
Comment[ja]=パラメトリック3D CAD
Comment[de]=Parametrische 3D-CAD-Arbeitsumgebung
Comment[fr]=Environnement de CAO 3D paramétrique
Comment[es]=Entorno CAD 3D paramétrico
Comment[ko]=파라메트릭 3D CAD
Comment[it]=Ambiente CAD 3D parametrico
Comment[pt_BR]=Ambiente CAD 3D paramétrico
Comment[zh_CN]=参数化三维 CAD
Comment[zh_TW]=參數化 3D CAD
Exec=/usr/bin/fullarccad %F
TryExec=/usr/bin/fullarccad
Icon=fullarccad
Terminal=false
Categories=Graphics;Engineering;3DGraphics;
MimeType=application/x-extension-fcstd;model/step;model/stl;model/obj;model/gltf+json;model/gltf-binary;
StartupNotify=true
Actions=Configure;

[Desktop Action Configure]
Name=Configure FreeCAD runtime
Name[ja]=FreeCADを設定
Exec=/usr/bin/fullarccad --configure
''',encoding='utf-8')
icons=root/'usr/share/icons/hicolor/scalable/apps';icons.mkdir(parents=True,exist_ok=True)
shutil.copy2(stage/'resources/fullarccad-native.svg',icons/'fullarccad.svg')
doc=root/'usr/share/doc/fullarccad';doc.mkdir(parents=True,exist_ok=True)
for name in ('README-ja.md','README-en.md','LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt','TERMS-ja.txt'):shutil.copy2(stage/name,doc/name)
for name in ('FREECAD-LICENSE.html','LGPL-2.1.txt','LICENSES-AND-SOURCES.md','LICENSE-REVIEW-STATUS.json'):shutil.copy2(runtime/name,doc/name)
(doc/'copyright').write_text('FullArcCAD distribution\n\n'+(stage/'TERMS-ja.txt').read_text(encoding='utf-8')+'\n\n'+(stage/'LEGACY_MIT_LICENSE.txt').read_text(encoding='utf-8')+'\n\n'+(stage/'THIRD_PARTY_NOTICES.txt').read_text(encoding='utf-8')+'\n\nOn Debian systems, the complete text of the GNU Lesser General Public License\nversion 2.1 can be found in /usr/share/common-licenses/LGPL-2.1.\nThe GNU General Public License version 3 is in /usr/share/common-licenses/GPL-3.\nSheetMetal and its bundled NetworkX dependency are excluded. Sheet metal\nfeatures are unavailable in this release.\n',encoding='utf-8')
def gzwrite(path,data):
 with path.open('wb') as raw:
  with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as f:f.write(data)
gzwrite(doc/'changelog.Debian.gz',('fullarccad ('+version+') unstable; urgency=low\n\n  * Add ten-language Linux native preview and desktop integration.\n  * Add first-run AppImage runtime preparation.\n\n -- FullArcCAD project <victriokook@gmail.com>  Sun, 01 Nov 2026 00:00:00 +0900\n').encode())
man=root/'usr/share/man/man1';man.mkdir(parents=True,exist_ok=True)
gzwrite(man/'fullarccad.1.gz',b'.TH FULLARCCAD 1 "November 2026" "FullArcCAD"\n.SH NAME\nfullarccad \\- parametric 3D CAD workspace\n.SH SYNOPSIS\n.B fullarccad\n.RI [ files... ]\n.SH OPTIONS\n.TP\n.B \\-configure\nSelect a compatible FreeCAD AppImage and prepare it for use.\n.TP\n.B \\-freecad PATH\nUse the specified FreeCAD x86_64 py311 AppImage or extracted AppRun.\n.TP\n.B \\-engine-info\nPrint validated runtime information.\n.TP\n.B \\-diagnose\nPrint the launch command without starting the CAD application.\n.TP\n.B \\-version\nPrint the application version.\n.TP\n.B \\-help\nPrint usage information.\n.SH FILES\nUser configuration is stored under XDG_CONFIG_HOME/fullarccad-native.\nEngine caches are stored under XDG_CACHE_HOME/fullarccad-native/engines.\nRemoving this package does not delete user models or caches.\n')
overrides=root/'usr/share/lintian/overrides';overrides.mkdir(parents=True,exist_ok=True)
(overrides/'fullarccad').write_text('# Local preview package, not a Debian archive initial upload; no WNPP bug exists.\nfullarccad: initial-upload-closes-no-bugs\n',encoding='utf-8')
control=root/'DEBIAN';control.mkdir(exist_ok=True)
depends=['python3 (>= 3.10)','libc6 (>= 2.35)','libgl1','libegl1','libglu1-mesa','libx11-xcb1','libxkbcommon-x11-0','libxcb-cursor0','libxcb-icccm4','libxcb-image0','libxcb-keysyms1','libxcb-render-util0','libxcb-xinerama0','libxcb-randr0','libxcb-shape0','libxcb-xfixes0','libfontconfig1','libdbus-1-3','zenity','xdg-utils','shared-mime-info','desktop-file-utils']
installed=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())//1024
(control/'control').write_text('Package: fullarccad\nVersion: '+version+'\nSection: graphics\nPriority: optional\nArchitecture: amd64\nMaintainer: FullArcCAD project <victriokook@gmail.com>\nInstalled-Size: '+str(installed)+'\nDepends: '+', '.join(depends)+'\nRecommends: fonts-noto-cjk, fonts-dejavu-core, libgl1-mesa-dri\nSuggests: ffmpeg\nDescription: Parametric 3D CAD workspace with ten interface languages\n Native FullArcCAD workspace with sketches, solids, surfaces, meshes,\n drawings and parameters. Uses an external FreeCAD x86_64 py311 AppImage.\n Includes first-run runtime selection and automatic AppImage extraction.\n',encoding='utf-8')
for p in root.rglob('*'):
 p.chmod(0o755 if p.is_dir() else 0o644)
for p in (bindir/'fullarccad',lib/'bootstrap.py',lib/'fullarccad'):p.chmod(0o755)
(control/'md5sums').write_text(''.join(hashlib.md5(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix()+'\n' for p in sorted(root.rglob('*')) if p.is_file() and 'DEBIAN' not in p.relative_to(root).parts),encoding='utf-8')
subprocess.run(['desktop-file-validate',str(desktop/'org.fullarccad.FullArcCAD.desktop')],check=True)
deb=out/('fullarccad_'+version+'_amd64.deb')
subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(deb)],check=True)
lint=subprocess.run(['lintian','--no-tag-display-limit',str(deb)],capture_output=True,text=True)
(r/'evidence/lintian.txt').write_text(lint.stdout+lint.stderr,encoding='utf-8')
archive=out/'FullArcCAD-License-Docs-v2-Linux-amd64.tar.gz'
with tarfile.open(archive,'w:gz',format=tarfile.PAX_FORMAT) as tar:
 for p in sorted(stage.rglob('*')):
  if p.is_file():
   info=tar.gettarinfo(str(p),'FullArcCAD-Linux-Native/'+p.relative_to(stage).as_posix());info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o755 if p.name in ('fullarccad','install','uninstall') else 0o644
   with p.open('rb') as f:tar.addfile(info,f)
for name in ('README-ja.md','README-en.md','TERMS-ja.txt','LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt'):shutil.copy2(stage/name,out/name)
(out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in (deb,archive)),encoding='utf-8')
print(json.dumps({'deb':deb.name,'deb_bytes':deb.stat().st_size,'tar':archive.name,'lintian_exit':lint.returncode}),flush=True)
