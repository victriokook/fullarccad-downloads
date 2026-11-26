from pathlib import Path
import subprocess,time,sys
from PIL import ImageGrab
proc=subprocess.Popen(['fullarccad'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
 deadline=time.monotonic()+20;window=None
 while time.monotonic()<deadline:
  p=subprocess.run(['xdotool','search','--name','^FullArcCAD$'],capture_output=True,text=True)
  if p.returncode==0 and p.stdout.strip():window=p.stdout.splitlines()[-1];break
  if proc.poll() is not None:raise RuntimeError('Setup ended before showing its window: '+str(proc.communicate()))
  time.sleep(.2)
 if window is None:raise TimeoutError('First-run setup did not show a window')
 time.sleep(.5);ImageGrab.grab().save(sys.argv[1])
 subprocess.run(['xdotool','windowfocus','--sync',window],check=True)
 subprocess.run(['xdotool','key','Escape'],check=True)
 proc.wait(timeout=15);assert proc.returncode==0
 assert not (Path.home()/'.config/fullarccad-native/launcher.json').exists()
 print('PASS: first-run runtime selection UI appears; cancel leaves configuration unchanged')
finally:
 if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
