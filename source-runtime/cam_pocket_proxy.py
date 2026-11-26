import sys
import FreeCAD as App
from pathlib import Path as FilePath
cam=str(FilePath(App.getHomePath())/'Mod/CAM')
if cam not in sys.path:sys.path.append(cam)
import Path
from Path.Op.PocketShape import ObjectPocket
from Path.Op.PocketBase import ObjectPocket as PocketBase
from Path.Op.Base import FeatureLocations

class GuardedPocket(ObjectPocket):
    def areaOpFeatures(self,obj):
        # Installed PocketShape uses super(self.__class__,self),which recurses in subclasses.
        return PocketBase.areaOpFeatures(self,obj)|FeatureLocations
    def execute(self,obj):
        try:
            import model_cam_pocket as m
            job=self.getJob(obj)
            source,tc,refs,bb,values,percent=m.parameters(job,int(obj.FullArcPocketFace),obj.StartDepth.Value,obj.FinalDepth.Value,obj.StepDown.Value,obj.SafeHeight.Value,obj.ClearanceHeight.Value,float(obj.StepOver),active=False)
            if list(obj.FullArcInputs)!=refs or obj.ToolController!=tc or len(obj.Base)!=1 or obj.Base[0][0]!=source or list(obj.Base[0][1])!=['Face'+str(obj.FullArcPocketFace)]:raise ValueError('Pocket references changed;recreate')
            if obj.ClearingPattern!='Offset' or obj.UseOutline or obj.UseRestMachining or obj.ExtraOffset.Value!=0 or obj.KeepToolDown or obj.UseStartPoint or obj.FinishDepth.Value!=0 or obj.ExtensionFeature:raise ValueError('Unsupported pocket mode;recreate')
            if not obj.Active:obj.Path=Path.Path([]);return
            super().execute(obj);m.check_path(obj,bb,tc.Tool.Diameter.Value/2,values)
        except Exception:
            obj.Path=Path.Path([])
            raise
