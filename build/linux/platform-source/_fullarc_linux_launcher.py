#!/usr/bin/env python3
"""FullArcCAD Linux launcher; no shell expansion, private local request queue."""
import argparse,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parent
EXTENSIONS={'.step','.stp','.fcstd','.stl','.glb','.gltf','.iges','.igs','.brep','.obj','.ply','.off'}
def xdg(name,default):return Path(os.environ.get(name,str(Path.home()/default))).expanduser().resolve()
def state_root():return Path(os.environ['FULLARCCAD_STATE_DIR']).resolve() if 'FULLARCCAD_STATE_DIR' in os.environ else xdg('XDG_STATE_HOME','.local/state')/'fullarccad-native'
def config_path():return xdg('XDG_CONFIG_HOME','.config')/'fullarccad-native/launcher.json'
def atomic_json(path,value):
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');os.chmod(tmp,0o600);tmp.replace(path)
def find_engine():
    configured=os.environ.get('FULLARCCAD_FREECAD')
    if not configured and config_path().is_file():configured=json.loads(config_path().read_text(encoding='utf-8')).get('engine')
    candidates=[configured,shutil.which('FreeCAD'),shutil.which('freecad'),'/opt/freecad/bin/FreeCAD','/opt/freecad/squashfs-root/AppRun']
    for candidate in candidates:
        if candidate:
            p=Path(candidate).expanduser().resolve()
            if p.is_file() and os.access(p,os.X_OK):return p
    raise RuntimeError('FreeCADが見つかりません。install.py --freecad /path/to/FreeCAD.AppImage で指定してください。')
def start_token(pid):
    directory=Path('/proc')/str(pid)
    if directory.stat().st_uid!=os.getuid():raise RuntimeError('Process owner mismatch')
    fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
    if fields[0] in ('Z','X'):raise ProcessLookupError('Exited process')
    return fields[19]
def alive(state,root=None):
    try:
        info=json.loads((state/'session.json').read_text());return start_token(int(info['pid']))==str(info['start_token']) and info['root']==str(root or ROOT)
    except (OSError,ValueError,KeyError,IndexError,RuntimeError):return False
def local_file(value):
    if value.startswith('file:'):
        uri=urlparse(value)
        if uri.netloc not in ('','localhost'):raise ValueError('Remote file URI is not supported')
        value=unquote(uri.path)
    path=Path(value).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in EXTENSIONS:raise ValueError('対応するCADファイルがありません: '+str(path))
    return str(path)
def main(argv=None):
    import fcntl
    parser=argparse.ArgumentParser(description='FullArcCAD Linux')
    parser.add_argument('--diagnose',action='store_true');parser.add_argument('files',nargs='*');args=parser.parse_args(argv)
    engine=find_engine();files=[local_file(x) for x in args.files];state=state_root();profile=state/'profile/user.cfg';macro=ROOT/'runtime/Launch.FCMacro'
    if not macro.is_file():raise RuntimeError('FullArcCAD runtime is missing')
    command=[str(engine),'--user-cfg',str(profile),str(macro)]
    if args.diagnose:print(json.dumps({'engine':str(engine),'command':command,'files':files,'state':str(state)},ensure_ascii=False));return 0
    state.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(state,0o700)
    for name in ('requests','responses','profile'):(state/name).mkdir(exist_ok=True,mode=0o700)
    with (state/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        atomic_json(state/'requests'/(uuid.uuid4().hex+'.json'),{'files':files})
        if not alive(state):
            for name in ('ready.json','startup_error.json'):(state/name).unlink(missing_ok=True)
            env=os.environ.copy();env['FULLARCCAD_STATE_DIR']=str(state);env['FREECAD_USER_HOME']=str(state/'freecad');env['FREECAD_USER_DATA']=str(state/'freecad/data');env['FREECAD_USER_TEMP']=str(state/'freecad/temp')
            with (state/'engine.log').open('ab') as log:
                process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
            atomic_json(state/'session.json',{'pid':process.pid,'start_token':start_token(process.pid),'root':str(ROOT)})
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        message=str(error);print(message,file=sys.stderr)
        notifier=shutil.which('zenity')
        if notifier:subprocess.Popen([notifier,'--error','--title=FullArcCAD','--text='+message])
        raise SystemExit(1)
