from pathlib import Path
import urllib.request,hashlib
p=Path('/work/assets/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage')
expected='3a853eb69ee595f779f2255dbf80a765926981d8ff68903cefee4dfb03a8f5ef'
if not p.exists():
 url='https://github.com/FreeCAD/FreeCAD/releases/download/1.1.3/'+p.name
 tmp=p.with_suffix('.download');digest=hashlib.sha256()
 with urllib.request.urlopen(url,timeout=60) as response,tmp.open('wb') as out:
  while True:
   data=response.read(4*1024*1024)
   if not data:break
   out.write(data);digest.update(data)
 if digest.hexdigest()!=expected:raise RuntimeError('Official FreeCAD fixture checksum mismatch')
 tmp.replace(p)
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
print('Verified official FreeCAD AppImage:',p.stat().st_size,'bytes',flush=True)
