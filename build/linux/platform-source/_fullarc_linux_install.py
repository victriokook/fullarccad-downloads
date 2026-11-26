#!/usr/bin/env python3
"""Per-user XDG installation; never changes mimeapps.list defaults."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRODUCT='789a2266-1eea-4510-82c6-fcc76bb903b8-linux-native'
MIMES=['model/step','application/step','application/x-step','application/x-extension-fcstd','model/stl','application/sla','model/gltf-binary','model/gltf+json','model/iges','application/iges','application/x-fullarccad-brep','model/obj','application/x-ply','application/x-off']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def xdg(name,default):return Path(os.environ.get(name,str(Path.home()/default))).expanduser().resolve()
def desktop_quote(value):
    if any(c in str(value) for c in '\n\r\t'):raise ValueError('Unsupported control character in desktop path')
    value=str(value).replace('%','%%')
    # Exec quoting is processed after Desktop Entry string-value escaping.
    escaped=''.join('\\'+c if c in '\\"`$' else c for c in value)
    return '"'+escaped.replace('\\','\\\\')+'"'
def refresh(data):
    warnings=[]
    for tool,target in (('update-mime-database',data/'mime'),('update-desktop-database',data/'applications')):
        executable=shutil.which(tool)
        if executable:
            proc=subprocess.run([executable,str(target)],capture_output=True,text=True)
            if proc.returncode:warnings.append(tool+': '+proc.stderr.strip())
        else:warnings.append(tool+' がありません。デスクトップ関連付けの反映には対応パッケージを導入してください。')
    return warnings
def install(engine=None):
    if sys.version_info<(3,10):raise RuntimeError('Python 3.10以上が必要です。')
    if engine:
        engine=Path(engine).expanduser().resolve()
        if not engine.is_file() or not os.access(engine,os.X_OK):raise RuntimeError('実行可能なFreeCADを指定してください: '+str(engine))
    data=xdg('XDG_DATA_HOME','.local/share');config=xdg('XDG_CONFIG_HOME','.config');home=Path.home().resolve();app=data/'fullarccad-native';marker=app/'install-manifest.json'
    from _fullarc_linux_launcher import alive,state_root
    if alive(state_root(),app):raise RuntimeError('FullArcCADを終了してからインストールしてください。')
    if app.is_symlink():raise RuntimeError('インストール先のシンボリックリンクには対応していません。')
    if app.exists() and any(app.iterdir()):
        if not marker.is_file() or json.loads(marker.read_text()).get('product_id')!=PRODUCT:raise RuntimeError('別の既存フォルダーへはインストールできません: '+str(app))
    files=[]
    def copy(source,target):
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);files.append({'path':str(target),'sha256':digest(target)})
    for source in ROOT.rglob('*'):
        relative=source.relative_to(ROOT)
        if not source.is_file() or '__pycache__' in relative.parts or source.suffix=='.pyc':continue
        if relative.parts[0] not in ('runtime','resources') and str(relative) not in ('bootstrap.py','fullarccad','install','uninstall','README-ja.md','LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt','TERMS-ja.txt','VERSION') and source.suffix!='.so':continue
        copy(source,app/relative)
    launcher=home/'.local/bin/fullarccad-native';launcher.parent.mkdir(parents=True,exist_ok=True)
    launcher.write_text('#!/bin/sh\nexec '+__import__('shlex').quote(str(app/'fullarccad'))+' \"$@\"\n',encoding='utf-8');launcher.chmod(0o755);files.append({'path':str(launcher),'sha256':digest(launcher)})
    desktop=data/'applications/org.fullarccad.FullArcCADNative.desktop';desktop.parent.mkdir(parents=True,exist_ok=True)
    desktop.write_text('[Desktop Entry]\nVersion=1.0\nType=Application\nName=FullArcCAD Native\nComment=CAD and mesh application powered by FreeCAD\nExec='+desktop_quote(app/'fullarccad')+' %F\nIcon=fullarccad-native\nTerminal=false\nStartupNotify=true\nCategories=Graphics;3DGraphics;Engineering;\nMimeType='+';'.join(MIMES)+';\n',encoding='utf-8');desktop.chmod(0o644);files.append({'path':str(desktop),'sha256':digest(desktop)})
    copy(ROOT/'resources/fullarccad-native.svg',data/'icons/hicolor/scalable/apps/fullarccad-native.svg')
    copy(ROOT/'resources/fullarccad-native-mime.xml',data/'mime/packages/fullarccad-native-mime.xml')
    preferences=config/'fullarccad-native/launcher.json';preferences.parent.mkdir(parents=True,exist_ok=True)
    if engine:
        preferences.write_text(json.dumps({'engine':str(engine)},ensure_ascii=False),encoding='utf-8')
    marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text(json.dumps({'product_id':PRODUCT,'version':'0.2.266-native.linux.preview1','app':str(app),'data':str(data),'home':str(home),'files':files},indent=2,ensure_ascii=False),encoding='utf-8')
    return {'app':str(app),'desktop_file':str(desktop),'launcher':str(launcher),'defaults_changed':False,'warnings':refresh(data)}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freecad');args=parser.parse_args()
    if os.environ.get('SUDO_USER'):raise RuntimeError('sudoを使わず、通常のユーザーで実行してください。')
    print(json.dumps(install(args.freecad),ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as error:print(str(error),file=sys.stderr);raise SystemExit(1)
