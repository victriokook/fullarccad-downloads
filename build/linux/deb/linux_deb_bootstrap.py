#!/usr/bin/env python3
"""Generic runtime locator/ABI bridge. CAD implementation lives in native modules."""
import os,sys,json,subprocess,shutil,hashlib,fcntl,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DOWNLOAD='https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3'
def xdg(name,default):return Path(os.environ.get(name,str(Path.home()/default))).expanduser()
CONFIG=xdg('XDG_CONFIG_HOME','.config')/'fullarccad-native/launcher.json'
CACHE=xdg('XDG_CACHE_HOME','.cache')/'fullarccad-native/engines'

def probe(app):
    code="import sys,struct,json; sys.path.insert(0,sys.argv[1]); import FreeCAD; print('FULLARCCAD_ENGINE='+json.dumps({'python':list(sys.version_info[:2]),'bits':struct.calcsize('P')*8,'implementation':sys.implementation.name,'freecad':FreeCAD.Version()}))"
    p=subprocess.run([str(app),'python','-c',code,str(app.parent/'usr/lib')],capture_output=True,text=True,timeout=45)
    lines=[line.partition('=')[2] for line in p.stdout.splitlines() if line.startswith('FULLARCCAD_ENGINE=')]
    if p.returncode or not lines:raise RuntimeError('This FreeCAD runtime could not be started. Choose the Linux x86_64 py311 AppImage from '+DOWNLOAD)
    info=json.loads(lines[-1])
    if info['python']!=[3,11] or info['bits']!=64 or info['implementation']!='cpython':
        raise RuntimeError('This FreeCAD runtime is incompatible. FullArcCAD needs the Linux x86_64 py311 AppImage (CPython 3.11, 64-bit).')
    return info

def extracted(candidate):
    candidate=candidate.expanduser().resolve()
    for app in (candidate,candidate.parent/'AppRun',candidate.parent.parent.parent/'AppRun'):
        if app.name=='AppRun' and app.is_file() and (app.parent/'usr/bin/python').is_file():return app
    return None

def prepare(candidate):
    candidate=Path(candidate).expanduser().resolve()
    app=extracted(candidate)
    if app:return app,probe(app)
    if not candidate.is_file():raise RuntimeError('FreeCAD file not found: '+str(candidate))
    with candidate.open('rb') as f:header=f.read(64)
    if header[:4]!=b'\x7fELF' or header[4]!=2 or header[8:11]!=b'AI\x02' or int.from_bytes(header[18:20],'little')!=62:
        raise RuntimeError('Select a Linux x86_64 FreeCAD AppImage, or an extracted AppRun.')
    digest=hashlib.sha256()
    with candidate.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):digest.update(block)
    folder=CACHE/digest.hexdigest();folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (folder/'.extract.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        app=folder/'squashfs-root/AppRun'
        if not (folder/'.ready').exists():
            image=folder/'FreeCAD.AppImage'
            if not image.exists():shutil.copyfile(candidate,image)
            image.chmod(0o700)
            subprocess.run([str(image),'--appimage-extract'],cwd=folder,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=300)
            info=probe(app)
            (folder/'.ready').write_text(json.dumps(info),encoding='utf-8')
            image.unlink()  # Original download is never changed.
        else:info=probe(app)
    return app,info

def save(app,info):
    CONFIG.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temp=CONFIG.with_suffix('.tmp')
    temp.write_text(json.dumps({'engine':str(app),'runtime':info},ensure_ascii=False,indent=2),encoding='utf-8');temp.chmod(0o600);temp.replace(CONFIG)

def choose():
    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')) or not shutil.which('zenity'):
        raise RuntimeError('FreeCAD is not configured. Run: fullarccad --configure --freecad /path/to/FreeCAD-py311.AppImage\nDownload: '+DOWNLOAD)
    answer=subprocess.run(['zenity','--question','--title=FullArcCAD','--text=FullArcCAD needs a compatible FreeCAD runtime. Select the Linux x86_64 py311 AppImage; it will be prepared automatically.','--ok-label=Select AppImage','--cancel-label=Cancel','--extra-button=Download FreeCAD'],capture_output=True,text=True)
    if answer.stdout.strip()=='Download FreeCAD':
        subprocess.Popen(['xdg-open',DOWNLOAD],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);raise SystemExit(0)
    if answer.returncode:raise SystemExit(0)
    selected=subprocess.run(['zenity','--file-selection','--title=Select FreeCAD Linux x86_64 py311 AppImage','--file-filter=FreeCAD AppImage | *.AppImage','--file-filter=All files | *'],capture_output=True,text=True)
    if selected.returncode or not selected.stdout.strip():raise SystemExit(0)
    return selected.stdout.strip()

def main():
    if len(sys.argv)<2:raise RuntimeError('Missing command')
    mode=sys.argv[1];args=sys.argv[2:]
    if mode not in ('fullarccad','install','uninstall'):raise RuntimeError('Unknown command')
    if '--help' in args or '-h' in args:
        print('Usage: fullarccad [CAD files...]\n       fullarccad --configure [--freecad FreeCAD-py311.AppImage]\n       fullarccad --engine-info\n       fullarccad --diagnose\n       fullarccad --version\nA compatible FreeCAD x86_64 py311 AppImage is prepared on first launch.');return 0
    if '--version' in args:print('FullArcCAD '+(ROOT/'VERSION').read_text().strip());return 0
    configure='--configure' in args
    if configure:args.remove('--configure')
    info_only='--engine-info' in args
    if info_only:args.remove('--engine-info')
    explicit=None
    if '--freecad' in args:
        i=args.index('--freecad')
        if i+1>=len(args):raise RuntimeError('--freecad needs a path')
        explicit=args[i+1]
        if mode=='fullarccad':del args[i:i+2]
    configured=None
    if CONFIG.is_file():configured=json.loads(CONFIG.read_text(encoding='utf-8')).get('engine')
    candidate=explicit or os.environ.get('FULLARCCAD_FREECAD') or (None if configure else configured)
    if candidate:app,info=prepare(candidate)
    else:
        app=None
        if not configure:
            for value in ('/opt/freecad/squashfs-root/AppRun','/opt/freecad/AppRun',shutil.which('FreeCAD'),shutil.which('freecad')):
                if not value:continue
                found=extracted(Path(value))
                if found:
                    try:info=probe(found);app=found;break
                    except RuntimeError:pass
        if app is None:
            if '--diagnose' in args or info_only:raise RuntimeError('FreeCAD is not configured. Use fullarccad --configure --freecad /path/to/FreeCAD-py311.AppImage')
            app,info=prepare(choose())
    if explicit or configure or not configured:save(app,info)
    if info_only:print(json.dumps({'engine':str(app),'runtime':info},ensure_ascii=False));return 0
    if configure:
        print('FreeCAD configured: '+str(app));return 0
    env=os.environ.copy();env['FULLARCCAD_FREECAD']=str(app);env['PYTHONDONTWRITEBYTECODE']='1'
    module={'fullarccad':'launcher','install':'install','uninstall':'uninstall'}[mode]
    code="import sys; sys.dont_write_bytecode=True; sys.path.insert(0,sys.argv.pop(1)); import importlib; m=importlib.import_module(sys.argv.pop(1)); m.main()"
    return subprocess.call([str(app),'python','-c',code,str(ROOT),'_fullarc_linux_'+module,*args],env=env)

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        message=str(error);print(message,file=sys.stderr)
        if os.environ.get('DISPLAY') and shutil.which('zenity') and '--diagnose' not in sys.argv and '--engine-info' not in sys.argv:
            subprocess.run(['zenity','--error','--title=FullArcCAD','--text='+message])
        raise SystemExit(2)
