from pathlib import Path
import subprocess,json,hashlib,tarfile,re,tempfile
r=Path('/work');root=r/'deb-root';stage=r/'stage';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
failures=[];elf=[]
for p in stage.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(stage);external=len(rel.parts)>2 and rel.parts[0]=='runtime' and rel.parts[1] in ('addons','solidworks_reader')
 if p.suffix in ('.pyd','.exe','.dll','.pyc','.pyo','.o','.a','.pdb','.debug'):failures.append(str(rel))
 if p.suffix in ('.c','.cpp','.h','.hpp') and not external:failures.append(str(rel))
 if p.suffix=='.py' and str(rel)!='bootstrap.py' and not external:failures.append(str(rel))
 if p.suffix.lower()=='.fcmacro' and str(rel)!='runtime/Launch.FCMacro':failures.append(str(rel))
 if p.suffix=='.so':
  sections=subprocess.check_output(['readelf','-S','-W',str(p)],text=True)
  assert '.debug_' not in sections and '.symtab' not in sections,str(rel)
  assert not subprocess.check_output(['patchelf','--print-rpath',str(p)],text=True).strip(),str(rel)
  elf.append(str(rel))
assert not failures,failures
assert len(elf)==435
assert len(list((root/'usr/lib/fullarccad/runtime').glob('*.so')))==432
assert len(list((root/'usr/lib/fullarccad').glob('*.so')))==1
assert not (root/'usr/lib/fullarccad/VALIDATION.json').exists()
deb=next((r/'output').glob('fullarccad_*_amd64.deb'))
with tempfile.TemporaryDirectory(prefix='fullarccad-deb-audit-') as tmp:
 extracted=Path(tmp);subprocess.run(['dpkg-deb','--extract',str(deb),str(extracted)],check=True)
 expected={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and 'DEBIAN' not in p.relative_to(root).parts}
 actual={p.relative_to(extracted).as_posix():sha(p) for p in extracted.rglob('*') if p.is_file()}
 assert actual==expected,'deb payload differs from audited package root'
control=subprocess.check_output(['dpkg-deb','-f',str(deb)],text=True)
assert 'Architecture: amd64' in control and 'victriokook@gmail.com' in control
for p in root.rglob('*'):
 if p.is_file() and 'DEBIAN' not in p.relative_to(root).parts:
  assert not p.stat().st_mode & 0o002,p
tar=next((r/'output').glob('*.tar.gz'))
with tarfile.open(tar) as archive:
 for member in archive:
  assert member.isfile() and '..' not in Path(member.name).parts and not Path(member.name).is_absolute()
  rel=Path(member.name).relative_to('FullArcCAD-Linux-Native')
  assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==sha(stage/rel)
report={'status':'PASS','stage_native_modules':435,'deb_application_modules':432,'deb_command_modules':1,'private_source_or_debug_files':failures,'ELF_debug_sections_absent':True,'ELF_RUNPATH_absent':True,'deb_payload_hash_roundtrip':True,'tar_hash_roundtrip':True,'deb_sha256':sha(deb),'tar_sha256':sha(tar),'native_source_sha256':{p.name:sha(p) for p in (r/'private-source').glob('*.py')},'stage_sha256':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()}}
(r/'evidence/SOURCE_PACKAGE_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if not k.endswith('sha256')},ensure_ascii=False),flush=True)
