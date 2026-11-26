"""Offline native LinuxCNC post for a single supported linear endmill operation."""
import importlib.util,math,hashlib
from pathlib import Path as FilePath
from types import SimpleNamespace
import FreeCAD as App,Path
from cam_post_values import validate_options
from model_cam_sim import snapshot

def data(op,precision=6):
    validate_options(precision,'preview.ngc')
    stock,tool,commands,stamp=snapshot(op,5.)
    tc=op.ToolController
    if type(tc.ToolNumber) is not int or not 1<=tc.ToolNumber<=999:raise ValueError('Tool number1..999 required')
    if not math.isfinite(float(tc.SpindleSpeed)) or not 0<float(tc.SpindleSpeed)<=100000:raise ValueError('Spindle speed outside limits')
    code=tc.Path.toGCode()
    tcommands=[Path.Command(x.Name,dict(x.Parameters)) for x in tc.Path.Commands if not x.Name.startswith('(')]
    if len(tcommands)!=2 or tcommands[0].Name!='M6' or tcommands[0].Parameters!={'T':float(tc.ToolNumber)} or tcommands[1].Name not in ('M3','M4') or tcommands[1].Parameters!={'S':float(tc.SpindleSpeed)}:raise ValueError('Native tool change and spindle commands required')
    job=op.Proxy.getJob(op)
    if str(getattr(job,'CoolantMode','None'))!='None' or str(getattr(op,'CoolantMode','None')) not in ('None','None/Off'):raise ValueError('Only coolant off supported')
    if commands[-1].Name!='G0' or commands[-1].Parameters.get('Z',-1e9)<=stock.BoundBox.ZMax:raise ValueError('Final clearance retract required')
    adapter=__import__('builtins')._fullarc_qt_slot(lambda name,cmds:SimpleNamespace(Name=name,Label=name,Path=Path.Path(cmds),Active=True,CoolantMode='None'),(2, 2, False, False))
    return [adapter('Tool',tcommands),adapter('Operation',commands)],(stamp,code,precision,tc.ToolNumber,float(tc.SpindleSpeed))

def generate(op,precision=6):
    objects,stamp=data(op,precision)
    path=FilePath(App.getHomePath())/'Mod/CAM/Path/Post/scripts/linuxcnc_post.py'
    if not path.is_file():raise ValueError('Bundled LinuxCNC post unavailable')
    spec=importlib.util.spec_from_file_location('fullarc_native_linuxcnc',str(path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    args='--no-show-editor --no-header --no-comments --precision '+str(precision)+' --preamble "G17 G54 G40 G49 G80 G90 G94"'
    text=module.export(objects,'-',args)
    if type(text) is not str or not text.strip().endswith('M2') or len(text)>2000000 or any(x not in text for x in ('G21','G90','G94','G43 H','M6','G1')):raise ValueError('Incomplete native post output')
    if data(op,precision)[1]!=stamp:raise ValueError('Inputs changed during generation')
    return text,stamp

def save(op,precision,filename,text,stamp):
    validate_options(precision,filename)
    current,current_stamp=generate(op,precision)
    if stamp!=current_stamp or text!=current:raise ValueError('Preview is stale;generate again')
    target=FilePath(filename)
    if not target.is_absolute() or not target.parent.is_dir():raise ValueError('Choose an absolute local file path')
    # Exclusive creation prevents accidental replacement,including symlinks.
    with target.open('x',encoding='ascii',newline='\n') as stream:stream.write(current)
    return str(target)
