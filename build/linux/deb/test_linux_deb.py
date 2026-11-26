from pathlib import Path
import subprocess,os,json,time,hashlib,signal,shutil,pwd
r=Path('/work');out=r/'evidence/deb-tests';out.mkdir(parents=True,exist_ok=True)
deb=next((r/'output').glob('fullarccad_*_amd64.deb'));version='0.2.266+licensefix.preview2-1';user='fac-test'
tests=[]
def record(name,details=True):
 tests.append({'name':name,'status':'PASS','details':details});(out/'RESULTS.json').write_text(json.dumps({'status':'RUNNING','tests':tests},ensure_ascii=False,indent=2))
 print('PASS: '+name,flush=True)
def rootrun(args,check=True):
 result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=900)
 if check and result.returncode:raise RuntimeError(repr(args)+'\n'+result.stdout[-3000:]+'\n'+result.stderr[-5000:])
 return result
home=Path('/home/fac-test');uid=pwd.getpwnam(user).pw_uid
os.chown(out,uid,uid)
env={'HOME':str(home),'USER':user,'LOGNAME':user,'QTWEBENGINE_DISABLE_SANDBOX':'1','LIBGL_ALWAYS_SOFTWARE':'1','QT_XCB_GL_INTEGRATION':'xcb_glx','QT_OPENGL':'software','PYTHONDONTWRITEBYTECODE':'1'}
def run(args,extra=None,check=True,timeout=240):
 values={**env,**(extra or {})}
 command=['runuser','-u',user,'--','env',*[k+'='+str(v) for k,v in values.items()],*map(str,args)]
 p=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError(repr(args)+'\n'+p.stdout[-3000:]+'\n'+p.stderr[-5000:])
 return p
try:
 assert not Path('/usr/bin/fullarccad').exists()
 sentinel=home/'keep-model.FCStd';sentinel.write_text('user model sentinel');os.chown(sentinel,uid,uid);original=hashlib.sha256(sentinel.read_bytes()).hexdigest()
 install=rootrun(['apt-get','install','-y',str(deb)]);(out/'apt-install.log').write_text(install.stdout+install.stderr)
 record('clean_apt_install_and_dependency_resolution',rootrun(['dpkg-query','-W','-f=${Version}','fullarccad']).stdout)
 assert not (home/'.config/fullarccad-native').exists()
 record('install_does_not_write_user_home')
 assert 'Usage:' in run(['fullarccad','--help']).stdout
 assert version in run(['fullarccad','--version']).stdout
 record('help_and_version_without_FreeCAD')
 assert rootrun(['dpkg-query','-W','-f=${Version}','fullarccad']).stdout==version
 assert Path('/usr/share/applications/org.fullarccad.FullArcCAD.desktop').is_file()
 assert Path('/usr/share/icons/hicolor/scalable/apps/fullarccad.svg').is_file()
 rootrun(['desktop-file-validate','/usr/share/applications/org.fullarccad.FullArcCAD.desktop'])
 record('desktop_and_icon_registration')
 missing=run(['fullarccad','--diagnose'],check=False)
 assert missing.returncode==2 and 'not configured' in missing.stderr
 record('missing_engine_is_actionable_without_traceback',missing.stderr.strip())
 run(['xvfb-run','-a','python3',r/'test_setup_ui.py',out/'first-run-setup.png'])
 record('first_run_setup_UI_and_cancel')
 image=r/'assets/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage'
 prepared=run(['fullarccad','--configure','--freecad',str(image)],timeout=600)
 info=json.loads(run(['fullarccad','--engine-info']).stdout)
 engine=Path(info['engine']);assert engine.is_relative_to(home/'.cache/fullarccad-native/engines')
 assert info['runtime']['python']==[3,11] and info['runtime']['bits']==64
 record('nonroot_real_AppImage_automatic_extraction',info)
 config=home/'.config/fullarccad-native/launcher.json';before=config.read_bytes()
 invalid=run(['fullarccad','--configure','--freecad','/does-not-exist.AppImage'],check=False)
 assert invalid.returncode==2 and config.read_bytes()==before
 record('failed_configuration_preserves_working_engine')
 diagnosis=json.loads(run(['fullarccad','--diagnose']).stdout);assert diagnosis['engine']==str(engine)
 record('installed_native_launcher_diagnosis',diagnosis)
 # A second explicit setup reuses the completed extraction without FUSE.
 run(['fullarccad','--configure','--freecad',str(image)],timeout=180)
 record('AppImage_cache_reuse')
 languages={'ja':'Japanese','en':'English','de':'German','zh-TW':'Chinese (Traditional)','es':'Spanish','fr':'French','zh-CN':'Chinese (Simplified)','ko':'Korean','it':'Italian','pt-BR':'Portuguese (Brazilian)'}
 runtime=Path('/usr/lib/fullarccad/runtime')
 for code,native in languages.items():
  state=out/code;state.mkdir();os.chown(state,uid,uid);cfg=state/'user.cfg'
  cfg.write_text('<?xml version="1.0" encoding="UTF-8"?><FCParameters><FCParamGroup Name="Root"><FCParamGroup Name="BaseApp"><FCParamGroup Name="Preferences"><FCParamGroup Name="FluxCAD"><FCText Name="Language">'+code+'</FCText></FCParamGroup><FCParamGroup Name="General"><FCText Name="Language">'+native+'</FCText></FCParamGroup></FCParamGroup></FCParamGroup></FCParamGroup></FCParameters>');os.chown(cfg,uid,uid)
  extra={'FULLARCCAD_STATE_DIR':state,'FULLARCCAD_TEST_RUNTIME':runtime,'FULLARCCAD_TEST_LANGUAGE':code,'FULLARCCAD_TEST_IMPORT_ALL':'1' if code=='en' else '0','FULLARCCAD_TEST_SWITCH':'1','FREECAD_USER_HOME':state,'FREECAD_USER_DATA':state/'data','FREECAD_USER_TEMP':state/'temp'}
  p=run(['xvfb-run','-a',engine,'--user-cfg',cfg,runtime/'Launch.FCMacro',r/'native_language_acceptance_linux.FCMacro'],extra=extra,check=False,timeout=180)
  (state/'stdout.log').write_text(p.stdout+p.stderr)
  report=json.loads((state/'acceptance.json').read_text());assert report['status']=='PASS',report
  record('native_language_'+code,report)
 # Reopen the last saved profile: pt-BR's menu action switched to ja.
 restart=out/'restart';restart.mkdir();os.chown(restart,uid,uid)
 extra.update(FULLARCCAD_STATE_DIR=restart,FULLARCCAD_TEST_LANGUAGE='ja',FULLARCCAD_TEST_IMPORT_ALL='0',FULLARCCAD_TEST_SWITCH='0',FREECAD_USER_HOME=restart,FREECAD_USER_DATA=restart/'data',FREECAD_USER_TEMP=restart/'temp')
 p=run(['xvfb-run','-a',engine,'--user-cfg',cfg,runtime/'Launch.FCMacro',r/'native_language_acceptance_linux.FCMacro'],extra=extra,check=False)
 (restart/'stdout.log').write_text(p.stdout+p.stderr);report=json.loads((restart/'acceptance.json').read_text());assert report['status']=='PASS',report;record('saved_language_real_restart',report)
 # Exercise app-native sketch proxies, STEP and reopen, not just FreeCAD primitives.
 cad=out/'cad';cad.mkdir();os.chown(cad,uid,uid)
 for mode in ('create','reopen'):
  state=cad/mode;state.mkdir();os.chown(state,uid,uid)
  more={'FAC_TEST_ROOT':'/usr/lib/fullarccad','FAC_TEST_OUT':cad,'FAC_TEST_MODE':mode,'FULLARCCAD_STATE_DIR':state,'FREECAD_USER_HOME':state,'FREECAD_USER_DATA':state/'data','FREECAD_USER_TEMP':state/'temp'}
  p=run(['xvfb-run','-a',engine,'--user-cfg',state/'user.cfg',r/'acceptance_cad.FCMacro'],extra=more,check=False)
  (state/'stdout.log').write_text(p.stdout+p.stderr);detail=json.loads((cad/(mode+'.json')).read_text());assert detail['pass'],detail;record('native_CAD_'+mode,detail)
 # Launch the installed /usr/bin entry point and open the saved model.
 state=out/'launcher';state.mkdir();os.chown(state,uid,uid)
 shell='exec fullarccad "$1"';values={**env,'FULLARCCAD_STATE_DIR':str(state)}
 command=['runuser','-u',user,'--','env',*[k+'='+str(v) for k,v in values.items()],'xvfb-run','-a','python3',str(r/'test_installed_launcher.py'),str(state),str(cad/'cut.FCStd')]
 p=subprocess.run(command,capture_output=True,text=True,timeout=150);(state/'stdout.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr;record('installed_command_file_open',json.loads((state/'launcher.json').read_text()))
 # Remove, then upgrade from a deliberately minimal older-version fixture.
 rootrun(['apt-get','remove','-y','fullarccad']);assert not Path('/usr/bin/fullarccad').exists();assert sentinel.read_bytes() and config.read_bytes();record('remove_preserves_user_data')
 fixture=r/'upgrade-fixture';(fixture/'DEBIAN').mkdir(parents=True,exist_ok=True);(fixture/'usr/share/doc/fullarccad').mkdir(parents=True,exist_ok=True)
 (fixture/'DEBIAN/control').write_text('Package: fullarccad\nVersion: 0.2.266+10lang.preview0-1\nArchitecture: amd64\nMaintainer: FullArcCAD project <victriokook@gmail.com>\nDescription: Local upgrade test fixture only\n')
 (fixture/'usr/share/doc/fullarccad/upgrade-fixture').write_text('test only')
 fixture_deb=r/'evidence/upgrade-fixture.deb';rootrun(['dpkg-deb','--root-owner-group','--build',fixture,fixture_deb]);rootrun(['apt-get','install','-y',fixture_deb]);rootrun(['apt-get','install','-y',deb])
 assert rootrun(['dpkg-query','-W','-f=${Version}','fullarccad']).stdout==version
 assert not Path('/usr/share/doc/fullarccad/upgrade-fixture').exists();assert config.read_bytes();record('upgrade_from_older_version_fixture')
 rootrun(['apt-get','purge','-y','fullarccad'])
 assert not Path('/usr/bin/fullarccad').exists() and not Path('/usr/share/applications/org.fullarccad.FullArcCAD.desktop').exists()
 assert hashlib.sha256(sentinel.read_bytes()).hexdigest()==original and config.is_file() and engine.is_file();record('purge_removes_package_and_preserves_user_files')
 result={'status':'PASS','environment':'clean Ubuntu 24.04 amd64 container / Xvfb / unprivileged GUI user','tests':tests}
except Exception:
 import traceback
 result={'status':'FAIL','tests':tests,'error':traceback.format_exc()}
(out/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'status':result['status'],'tests':len(tests),'error':result.get('error')},ensure_ascii=False),flush=True)
if result['status']!='PASS':raise SystemExit(1)
