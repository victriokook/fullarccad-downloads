from pathlib import Path
import os,json,hashlib,shutil,subprocess
from setuptools import Extension,Distribution
from Cython.Build import cythonize
r=Path('/work');source=r/'private-source';runtime=r/'stage/runtime';baseline=r/'baseline'
audit=json.loads((baseline/'audit.json').read_text());headers=Path('/opt/fullarc-python-headers')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pending=[];reused=[]
for p in sorted(source.glob('*.py')):
 previous=baseline/'native-source'/p.name;command=p.stem.startswith('_fullarc_linux_')
 folder=baseline/'stage' if command else baseline/'stage/runtime';binaries=list(folder.glob(p.stem+'.*.so'))
 if previous.exists() and previous.read_bytes()==p.read_bytes() and len(binaries)==1:
  binary=binaries[0];key=binary.relative_to(baseline/'stage').as_posix()
  assert sha(binary)==audit['files'][key],key
  shutil.copy2(binary,runtime/binary.name);reused.append(p.stem)
 else:
  pending.append(Extension(p.stem,[str(p)],include_dirs=[str(headers/'Include'),str(headers)],define_macros=[('CYTHON_CLINE_IN_TRACEBACK','0')],extra_compile_args=['-O2','-g0','-fvisibility=hidden','-ffile-prefix-map=/work=build'],extra_link_args=['-Wl,--strip-all']))
print('Native compilation:',len(pending),'compile /',len(reused),'verified reuse',flush=True)
extensions=cythonize(pending,build_dir=str(r/'private-c'),nthreads=4,compiler_directives={'emit_code_comments':False,'language_level':3,'binding':True,'annotation_typing':False,'infer_types':False,'embedsignature':False},quiet=True)
dist=Distribution({'name':'FullArcCADLinuxNative','ext_modules':extensions});cmd=dist.get_command_obj('build_ext');cmd.build_lib=str(runtime);cmd.build_temp=str(r/'private-objects');cmd.parallel=4;cmd.ensure_finalized();cmd.run()
for p in source.glob('*.py'):
 binaries=list(runtime.glob(p.stem+'.*.so'));assert len(binaries)==1,p.stem
 subprocess.run(['strip','--strip-all',str(binaries[0])],check=True)
 if p.stem.startswith('_fullarc_linux_'):shutil.copy2(binaries[0],r/'stage'/binaries[0].name);binaries[0].unlink()
assert len(list(runtime.glob('*.so')))==432
info={'version':'0.2.266+licensefix.preview2-1','platform':'linux-amd64','application_modules':432,'command_modules':3,'compiled':len(pending),'reused_verified':len(reused),'languages':['ja','en','de','zh-TW','es','fr','zh-CN','ko','it','pt-BR']}
(r/'stage/BUILD_INFO.json').write_text(json.dumps(info,indent=2));(r/'stage/VERSION').write_text(info['version']+'\n');(runtime/'VERSION').write_text(info['version']+'\n')
(r/'evidence/BUILD_INFO.json').write_text(json.dumps(info,indent=2))
print(json.dumps(info),flush=True)
