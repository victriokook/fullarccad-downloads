import sys
from pathlib import Path as FilePath
import FreeCAD as App
cam=str(FilePath(App.getHomePath())/'Mod/CAM')
if cam not in sys.path:sys.path.append(cam)
import Path
from Path.Op.Drilling import ObjectDrilling

class GuardedDrilling(ObjectDrilling):
    def execute(self,obj):
        try:
            import model_cam_drill as m
            job=self.getJob(obj);src,tc,refs,data,v=m.parameters(job,int(obj.FullArcDrillFace),obj.StartDepth.Value,obj.FinalDepth.Value,obj.RetractHeight.Value,obj.ClearanceHeight.Value,active=False)
            if list(obj.FullArcInputs)!=refs or obj.ToolController!=tc or len(obj.Base)!=1 or obj.Base[0][0]!=src or list(obj.Base[0][1])!=['Face'+str(obj.FullArcDrillFace)]:raise ValueError('Drilling references changed')
            if tc.Tool.Proxy.get_shape_name().lower()!='drill' or abs(tc.Tool.Diameter.Value-data[4])>1e-7 or tc.Tool.Length.Value<v['start']-v['final']+10:raise ValueError('Invalid drilling tool')
            if obj.PeckEnabled or obj.DwellEnabled or obj.AddTipLength or obj.KeepToolDown or obj.ExtraOffset!='None' or obj.chipBreakEnabled or obj.feedRetractEnabled or abs(obj.SafeHeight.Value-v['retract'])>1e-7:raise ValueError('Only normal G81 cycle supported')
            if obj.Locations or obj.Disabled:raise ValueError('Additional or disabled holes unsupported')
            if not obj.Active:obj.Path=Path.Path([]);return
            super().execute(obj);m.check_path(obj,data,v,tc.VertFeed.Value)
        except Exception:obj.Path=Path.Path([]);raise
