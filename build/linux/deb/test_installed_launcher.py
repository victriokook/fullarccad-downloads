from pathlib import Path
import os,sys,subprocess,json,time,signal
state=Path(sys.argv[1]);model=Path(sys.argv[2]);proc=subprocess.run(['fullarccad',str(model)],capture_output=True,text=True,timeout=60)
assert proc.returncode==0,proc.stderr
deadline=time.monotonic()+70;pid=None
try:
 while time.monotonic()<deadline:
  if (state/'session.json').exists():pid=json.loads((state/'session.json').read_text())['pid']
  if (state/'startup_error.json').exists():raise RuntimeError((state/'startup_error.json').read_text())
  responses=list((state/'responses').glob('*.json')) if (state/'responses').exists() else []
  if responses:
   report=json.loads(responses[0].read_text());assert report.get('results') and all(x['status']=='OPEN' for x in report['results']),report
   (state/'launcher.json').write_text(json.dumps(report,indent=2));break
  time.sleep(.5)
 else:raise TimeoutError('Installed launcher did not open the model')
finally:
 if pid:
  try:os.kill(pid,signal.SIGTERM)
  except OSError:pass
