"""Private Windows build. Never uploads sources or artifacts."""
from pathlib import Path
import argparse, ast, hashlib, json, os, shutil, struct, subprocess, sys, time, zipfile
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
RELEASE="0.2.266-native.license-mitigation.preview2"

def run(args, **kwargs):
    print('+',subprocess.list2cmdline([str(a) for a in args]),flush=True)
    subprocess.run([str(a) for a in args],check=True,**kwargs)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=PROJECT/'source-runtime')
    parser.add_argument('--freecad',type=Path)
    parser.add_argument('--release-id',default=RELEASE)
    parser.add_argument('--label',default='7languages')
    parser.add_argument('--baseline',type=Path)
    options=parser.parse_args()
    if sys.platform!='win32' or sys.version_info[:2]!=(3,11) or struct.calcsize('P')!=8:
        raise RuntimeError('Run with 64-bit Python 3.11 on Windows: py -3.11 build_native.py')
    private=PROJECT/'work'/'native-build';private.mkdir(parents=True,exist_ok=True)
    from Cython.Build import cythonize
    from setuptools import Extension, Distribution
    source=options.source.resolve()
    required=['FluxCAD.FCMacro','fluxcad.py','icons','addons','templates','solidworks_reader']
    for name in required:
        if not (source/name).exists():raise FileNotFoundError(source/name)
    stamp=options.label+'-'+time.strftime('%Y%m%d-%H%M%S');build=private/stamp;build.mkdir(exist_ok=True)
    stage=build/'stage';stage.mkdir(exist_ok=True);runtime=stage/'runtime';runtime.mkdir(exist_ok=True)
    work=build/'native-source';work.mkdir(exist_ok=True)
    # Sources and generated C remain private; the distribution receives only .pyd.
    for p in source.glob('*.py'):shutil.copy2(p,work/p.name) if not (work/p.name).exists() or p.read_bytes()!=(work/p.name).read_bytes() else None
    (work/'_fullarc_entry.py').write_text((source/'FluxCAD.FCMacro').read_text(encoding='utf-8-sig'),encoding='utf-8')
    launch=(ROOT/'Launch.FCMacro').read_text(encoding='utf-8-sig')
    old="runpy.run_path(str(_root/'FluxCAD.FCMacro'),run_name='__main__')"
    if old not in launch:raise RuntimeError('Unexpected Launch.FCMacro; refusing to package unprotected source')
    (work/'_fullarc_launch.py').write_text(launch.replace(old,'import _fullarc_entry'),encoding='utf-8')
    os.chdir(work)
    modules=[Extension(p.stem,[p.name],define_macros=[('CYTHON_CLINE_IN_TRACEBACK','0')],extra_compile_args=['/O2','/Brepro'],extra_link_args=['/DEBUG:NONE','/Brepro']) for p in sorted(work.glob('*.py'))]
    pending=[];reused=[]
    baseline=options.baseline
    audit=json.loads((baseline/'audit-final-portable.json').read_text(encoding='utf-8')) if baseline else {}
    if baseline and audit.get('status')!='PASS':raise RuntimeError('Baseline audit is not PASS')
    for module in modules:
        previous=baseline/'native-source'/(module.name+'.py') if baseline else None
        binaries=list((baseline/'stage/runtime').glob(module.name+'.*.pyd')) if baseline else []
        if previous and previous.is_file() and previous.read_bytes()==(work/(module.name+'.py')).read_bytes() and len(binaries)==1:
            binary=binaries[0];key='runtime/'+binary.name
            if hashlib.sha256(binary.read_bytes()).hexdigest()!=audit['sha256'].get(key):raise RuntimeError('Baseline binary mismatch: '+key)
            shutil.copy2(binary,runtime/binary.name);reused.append(module.name)
        else:pending.append(module)
    print('Native modules: '+str(len(pending))+' compile / '+str(len(reused))+' verified cache',flush=True)
    ext=cythonize(pending,build_dir=str(build/'c'),nthreads=min(4,os.cpu_count() or 1),compiler_directives={'emit_code_comments':False,'language_level':3,'binding':True,'annotation_typing':False,'infer_types':False,'embedsignature':False},quiet=True)
    from setuptools._distutils._msvccompiler import MSVCCompiler
    try:
        compiler=MSVCCompiler();compiler.initialize(plat_name='win-amd64')
    except Exception as exc:
        raise RuntimeError('Microsoft C++ Build Tools is required. Install the Desktop development with C++ workload, MSVC x64/x86 and Windows SDK, then rerun this file.') from exc
    dist=Distribution({'name':'FullArcCADNative','ext_modules':ext});cmd=dist.get_command_obj('build_ext')
    cmd.build_lib=str(runtime);cmd.build_temp=str(build/'objects');cmd.parallel=min(4,os.cpu_count() or 1)
    cmd.ensure_finalized();cmd.run()
    for module in modules:
        if len(list(runtime.glob(module.name+'.*.pyd')))!=1:raise RuntimeError('Missing compiled module: '+module.name)
    from strip_pe_debug import strip
    for native in runtime.glob('*.pyd'):strip(native)
    for name in ('icons','addons','templates','solidworks_reader','examples'):
        if (source/name).is_dir():shutil.copytree(source/name,runtime/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    # Retain original notices and non-code data, including templates/translations.
    for p in source.iterdir():
        if p.is_file() and p.suffix.lower() not in ('.py','.pyc','.pyo','.fcmacro','.c','.cpp','.pdb'):
            shutil.copy2(p,runtime/p.name)
    bootstrap=(ROOT/'QtBootstrap.txt').read_text(encoding='utf-8')
    (runtime/'Launch.FCMacro').write_text(bootstrap,encoding='utf8')
    for name in ('LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt','利用条件.txt'):shutil.copy2(ROOT/name,stage/name)
    csc=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not csc.exists():raise FileNotFoundError(csc)
    common=(ROOT/'Common.cs').read_text(encoding='utf8')
    # Separate target prevents a previous source-bearing installation contaminating this build.
    common=common.replace('Path.Combine(Local,"Programs","FullArcCAD")','Path.Combine(Local,"Programs","FullArcCAD-Native")')
    common=common.replace('0.2.266-alpha.windows1',options.release_id)
    commonfile=build/'Common.cs';commonfile.write_text(common,encoding='utf8')
    launcher=(ROOT/'Launcher.cs').read_text(encoding='utf8')
    needle='if(!File.Exists(engine))throw new IOException("FreeCADが見つかりません。セットアップでFreeCADの場所を指定してください。");'
    replacement='''if(!File.Exists(engine)){
        string config=Path.Combine(state,"engine.json");
        if(File.Exists(config)){object v;var j=Common.ReadJson(config);if(j.TryGetValue("engine",out v))engine=Convert.ToString(v);}
        if(!File.Exists(engine))using(var dialog=new OpenFileDialog{Title="FreeCAD (Python 3.11) を選択",Filter="FreeCAD|FreeCAD.exe"}){
            if(dialog.ShowDialog()!=DialogResult.OK)return 0;
            engine=dialog.FileName;Common.WriteJson(config,new {engine=engine});
        }
    }'''
    if needle not in launcher:raise RuntimeError('Unexpected launcher version')
    launcher=launcher.replace(needle,replacement)
    launcherfile=build/'Launcher.cs';launcherfile.write_text(launcher,encoding='utf8')
    refs=['System.Windows.Forms.dll','System.Drawing.dll','System.Web.Extensions.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll','System.Core.dll']
    def compile_cs(src,target,payload=None):
        args=[csc,'/nologo','/target:winexe','/optimize+','/platform:anycpu','/utf8output','/win32icon:'+str(ROOT/'FullArcCAD.ico'),'/out:'+str(target)]
        args+=['/reference:'+r for r in refs]
        if payload:args+=['/resource:'+str(payload)+',FullArcCAD.Payload.zip']
        run([*args,commonfile,src])
    compile_cs(launcherfile,stage/'FullArcCAD.exe')
    compile_cs(ROOT/'Uninstall.cs',stage/'FullArcCAD-Uninstall.exe')
    forbidden=[str(p.relative_to(runtime)) for p in runtime.glob('*') if p.is_file() and p.suffix.lower() in ('.py','.pyc','.pyo','.c','.cpp','.pdb')]
    macros=list(runtime.glob('*.FCMacro'))
    if forbidden or macros!=[runtime/'Launch.FCMacro']:raise RuntimeError('Source leak audit failed: '+repr(forbidden))
    language_tree=ast.parse((source/'i18n.py').read_text(encoding='utf-8-sig'))
    language_codes=[key.value for node in language_tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='LANGUAGES' for target in node.targets) for key in node.value.keys]
    info={'version':options.release_id,'source':str(source),'python':sys.version,'compiled_modules':len(modules),'newly_compiled':len(pending),'verified_reused':len(reused),'languages':language_codes,'native_compile':True,'windows_startup':'not_tested','notes':'Third-party source and license notices retained; native binaries are not immune to reverse engineering.'}
    freecad=options.freecad
    if freecad:
        if not freecad.is_file():raise FileNotFoundError(freecad)
        state=build/'smoke-state';state.mkdir();env=os.environ.copy();env['FULLARCCAD_STATE_DIR']=str(state)
        env['FREECAD_USER_HOME']=str(state);env['FREECAD_USER_DATA']=str(state/'data');env['FREECAD_USER_TEMP']=str(state/'temp')
        proc=subprocess.Popen([str(freecad),'--user-cfg',str(state/'user.cfg'),str(runtime/'Launch.FCMacro')],env=env,cwd=stage,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if (state/'startup_error.json').exists():raise RuntimeError((state/'startup_error.json').read_text())
            if (state/'ready.json').exists():info['windows_startup']='ready_marker_passed';break
            if proc.poll() is not None:raise RuntimeError('FreeCAD exited before readiness')
            time.sleep(1)
        else:raise RuntimeError('FreeCAD startup timed out; no distribution generated')
        proc.terminate();proc.wait(timeout=20)
        # This isolated smoke process owns no user documents.
    (runtime/'VERSION').write_text(options.release_id+'\n',encoding='utf8')
    (stage/'BUILD_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
    out=PROJECT/'releases'/stamp;out.mkdir(parents=True,exist_ok=True)
    def archive(folder,path):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.rglob('*')):
                if p.is_file():z.write(p,p.relative_to(folder).as_posix())
        with zipfile.ZipFile(path) as z:
            if z.testzip():raise RuntimeError('ZIP integrity failed')
    payload=build/'installer-payload.zip';archive(stage,payload)
    compile_cs(ROOT/'Setup.cs',out/'FullArcCAD-Setup-Native-Preview.exe',payload)
    portable=build/'portable';shutil.copytree(stage,portable,dirs_exist_ok=True);(portable/'FullArcCAD-Uninstall.exe').unlink(missing_ok=True)
    pp=build/'portable-payload.zip';archive(portable,pp)
    compile_cs(ROOT/'Portable.cs',out/'FullArcCAD-Portable-Native-Preview.exe',pp)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.exe')}
    (out/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()),encoding='ascii')
    (out/'BUILD_REPORT.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
    for name in ('LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt','利用条件.txt'):shutil.copy2(ROOT/name,out/name)
    print('\nBuild completed: '+str(out),flush=True)
    print('Not published. Review BUILD_REPORT.json and run functional checks before distribution.',flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        log=ROOT/'BUILD-ERROR.txt';log.write_text(traceback.format_exc(),encoding='utf8');print(log.read_text(),file=sys.stderr);sys.exit(1)

