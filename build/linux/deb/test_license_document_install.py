from pathlib import Path
import json,subprocess,hashlib
r=Path('/work');result={'status':'FAIL','checks':[]}
def check(name,ok):
    assert ok,name
    result['checks'].append({'name':name,'status':'PASS'});print('PASS: '+name,flush=True)
try:
    deb=next((r/'output').glob('*.deb'))
    p=subprocess.run(['apt-get','-o','Dpkg::Options::=--path-include=/usr/share/doc/*','install','-y',str(deb)],capture_output=True,text=True,timeout=900)
    (r/'evidence/ACTUAL-INSTALL.log').write_text(p.stdout+p.stderr)
    check('actual_clean_deb_install',p.returncode==0)
    check('installed_version',subprocess.check_output(['fullarccad','--version'],text=True).strip()=='FullArcCAD 0.2.266+licensefix.preview2-1')
    for name in ('FREECAD-LICENSE.html','LGPL-2.1.txt','LICENSES-AND-SOURCES.md','LICENSE-REVIEW-STATUS.json'):
        a=r/'stage/runtime'/name
        check('installed_runtime_license_'+name,Path('/usr/lib/fullarccad/runtime',name).read_bytes()==a.read_bytes())
        check('installed_doc_license_'+name,Path('/usr/share/doc/fullarccad',name).read_bytes()==a.read_bytes())
    check('third_party_reader_MIT_retained','MIT License' in Path('/usr/lib/fullarccad/runtime/solidworks_reader/LICENSE').read_text())
    check('excluded_addon_absent',not Path('/usr/lib/fullarccad/runtime/addons/SheetMetal').exists())
    check('legacy_rights_preserved','MIT' in Path('/usr/share/doc/fullarccad/LEGACY_MIT_LICENSE.txt').read_text())
    p=subprocess.run(['apt-get','remove','-y','fullarccad'],capture_output=True,text=True,timeout=120);check('remove_package',p.returncode==0)
    result['status']='PASS'
except Exception:
    import traceback;result['error']=traceback.format_exc()
(r/'evidence/ACTUAL-LICENSE-DOC-INSTALL.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if result['status']!='PASS':raise SystemExit(1)
