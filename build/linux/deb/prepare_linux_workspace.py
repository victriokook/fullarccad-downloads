"""Prepare a Linux/deb snapshot from the canonical project; no historical C-drive sources needed."""
from pathlib import Path
import argparse,shutil,json,datetime
parser=argparse.ArgumentParser()
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[3])
parser.add_argument('--workdir',type=Path)
parser.add_argument('--baseline',type=Path,help='Optional verified native-source/stage/audit.json cache')
args=parser.parse_args();project=args.project.resolve();recipes=project/'build/linux/deb'
dest=args.workdir or project/'work'/('linux-deb-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
if dest.exists():raise RuntimeError('Refusing to merge into an existing workspace: '+str(dest))
dest.mkdir(parents=True);source=project/'source-runtime'
shutil.copytree(source,dest/'source-runtime',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
private=dest/'private-source';private.mkdir()
for p in source.glob('*.py'):shutil.copy2(p,private/p.name)
(private/'_fullarc_entry.py').write_text((source/'FluxCAD.FCMacro').read_text(encoding='utf-8-sig'),encoding='utf-8')
for p in (project/'build/linux/platform-source').glob('_fullarc_linux_*.py'):shutil.copy2(p,private/p.name)
stage=dest/'stage';runtime=stage/'runtime';runtime.mkdir(parents=True)
for name in ('addons','icons','templates','solidworks_reader','examples'):shutil.copytree(source/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for p in source.iterdir():
 if p.is_file() and p.suffix.lower() not in ('.py','.pyc','.pyd','.fcmacro','.c','.pdb'):shutil.copy2(p,runtime/p.name)
shutil.copy2(project/'build/windows/QtBootstrap.txt',runtime/'Launch.FCMacro')
shutil.copy2(recipes/'linux_deb_bootstrap.py',stage/'bootstrap.py')
shutil.copytree(recipes/'assets',stage/'resources')
for name in ('LEGACY_MIT_LICENSE.txt','THIRD_PARTY_NOTICES.txt'):shutil.copy2(project/'build/windows'/name,stage/name)
shutil.copy2(project/'build/windows/利用条件.txt',stage/'TERMS-ja.txt')
for mode in ('fullarccad','install','uninstall'):
 (stage/mode).write_text('#!/bin/sh\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec python3 "$HERE/bootstrap.py" '+mode+' "$@"\n',encoding='utf-8',newline='\n')
if args.baseline:shutil.copytree(args.baseline,dest/'baseline')
else:
 (dest/'baseline/native-source').mkdir(parents=True);(dest/'baseline/stage/runtime').mkdir(parents=True)
 (dest/'baseline/audit.json').write_text(json.dumps({'files':{}}))
for name in ('output','assets','evidence'):(dest/name).mkdir()
for name in ('build_linux_deb_native.py','package_linux_deb.py','audit_linux_deb.py','test_linux_deb.py','test_setup_ui.py','test_installed_launcher.py','fetch_freecad_fixture.py','linux_deb_bootstrap.py','native_language_acceptance_linux.FCMacro','acceptance_cad.FCMacro'):shutil.copy2(recipes/name,dest/name)
(project/'work/LINUX_DEB_WORKSPACE.txt').write_text(str(dest),encoding='utf-8')
print(dest)
