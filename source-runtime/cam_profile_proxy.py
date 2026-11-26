import sys
import FreeCAD as App
from pathlib import Path as FilePath
cam=str(FilePath(App.getHomePath())/'Mod/CAM')
if cam not in sys.path:sys.path.append(cam)
import Path
from Path.Op.Profile import ObjectProfile

class GuardedProfile(ObjectProfile):
    def execute(self,obj):
        try:
            import model_cam_profile as m
            from cam_depth_values import validate_depths
            job=self.getJob(obj);source,tc=m.inputs(job,active=False)
            expected=[source,job.Stock,tc,tc.Tool]+list(getattr(source,'Objects',[]))
            if list(obj.FullArcInputs)!=expected or obj.ToolController!=tc:raise ValueError('CAM inputs changed; recreate contour')
            if obj.Base or obj.Side!='Outside' or not obj.UseComp or not obj.processPerimeter or obj.processHoles or obj.processCircles:raise ValueError('Only whole exterior compensated contour supported')
            validate_depths(obj.StartDepth.Value,obj.FinalDepth.Value,obj.StepDown.Value,obj.SafeHeight.Value,obj.ClearanceHeight.Value)
            if obj.FinalDepth.Value<source.Shape.BoundBox.ZMin-1e-7 or obj.FinalDepth.Value>=source.Shape.BoundBox.ZMax or obj.StartDepth.Value<source.Shape.BoundBox.ZMax-1e-7 or obj.SafeHeight.Value<=job.Stock.Shape.BoundBox.ZMax:raise ValueError('Invalid model depths or safe height')
            super().execute(obj)
            if not obj.Path.Commands:raise ValueError('Native contour has no path')
        except Exception:
            obj.Path=Path.Path([])
            raise
