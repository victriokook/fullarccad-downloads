#!/usr/bin/env python3
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
PRODUCT='789a2266-1eea-4510-82c6-fcc76bb903b8-linux-native'
def remove(app):
    app=Path(app).resolve();manifest=app/'install-manifest.json';info=json.loads(manifest.read_text(encoding='utf-8'))
    if info.get('product_id')!=PRODUCT or Path(info['app']).resolve()!=app:raise RuntimeError('FullArcCADのインストール先ではありません。')
    data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share'))).expanduser().resolve();home=Path.home().resolve()
    if app!=data/'fullarccad-native' or info['data']!=str(data) or info['home']!=str(home):raise RuntimeError('現在のユーザーのインストール先ではありません。')
    from _fullarc_linux_launcher import alive,state_root
    if alive(state_root(),app):raise RuntimeError('FullArcCADを終了してからアンインストールしてください。')
    # Refuse to remove files outside these known, product-owned locations.
    extra={home/'.local/bin/fullarccad-native',data/'applications/org.fullarccad.FullArcCADNative.desktop',data/'icons/hicolor/scalable/apps/fullarccad-native.svg',data/'mime/packages/fullarccad-native-mime.xml'}
    candidates=[]
    for entry in info['files']:
        path=Path(entry['path']);resolved=path.resolve()
        if not resolved.is_relative_to(app) and resolved not in extra:raise RuntimeError('Unsafe uninstall manifest path: '+str(path))
        candidates.append((path,entry['sha256']))
    removed=0;kept=[]
    for path,expected in candidates:
        if not path.is_file():continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:kept.append(str(path));continue
        path.unlink();removed+=1
        if path.suffix=='.py':
            cache=path.parent/'__pycache__'
            if cache.is_dir():
                for pyc in cache.glob(path.stem+'.*.pyc'):
                    if pyc.resolve().is_relative_to(app):pyc.unlink()
    manifest.unlink()
    for path in sorted((p for p in app.rglob('*') if p.is_dir() and not p.is_symlink()),key=lambda p:len(p.parts),reverse=True):
        if not any(path.iterdir()):path.rmdir()
    if not any(app.iterdir()):app.rmdir()
    for tool,path in (('update-mime-database',data/'mime'),('update-desktop-database',data/'applications')):
        if shutil.which(tool):subprocess.run([tool,str(path)],capture_output=True)
    return {'removed_files':removed,'kept_modified_files':kept,'preferences_and_defaults_preserved':True}
if __name__=='__main__':
    try:print(json.dumps(remove(Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
    except Exception as error:print(str(error),file=sys.stderr);raise SystemExit(1)

def main():
    print(json.dumps(remove(Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
