"""Imprint a finite on-face wire without changing the solid's occupied volume."""
import re
import Part
from BOPTools import SplitAPI
from split_face_counts import checked_face_counts
from i18n import tr


def unwrap(shape, kinds):
    for _ in range(8):
        if shape.ShapeType in kinds:
            return shape
        if shape.ShapeType != 'Compound' or len(shape.childShapes()) != 1:
            break
        shape=shape.childShapes()[0]
    raise ValueError(tr('単一ソリッドと、1本の辺またはワイヤを指定してください。',
                        'Specify one solid and one edge or wire.'))


def build(source, face_name, tool):
    if not isinstance(face_name,str) or not re.fullmatch(r'Face[1-9][0-9]{0,5}',face_name):
        raise ValueError('Select an indexed FaceN')
    if source.isNull() or tool.isNull() or not source.isValid() or not tool.isValid():
        raise ValueError('Repair invalid input geometry')
    solid=unwrap(source,('Solid',))
    if len(source.Faces)>200:
        raise ValueError('Source exceeds 200 faces')
    # Resolve on the original wrapper to preserve the user's FaceN numbering.
    try:face=source.getElement(face_name)
    except Exception:raise ValueError('The selected face is missing') from None
    if not isinstance(face.Surface,(Part.Plane,Part.Cylinder)):
        raise ValueError(tr('平面または円柱面を選択してください。', 'Select a planar or cylindrical face.'))
    wire=unwrap(tool,('Edge','Wire'))
    if wire.ShapeType=='Edge':wire=Part.Wire([wire])
    if not 1<=len(wire.Edges)<=200 or wire.Length<=1e-7:
        raise ValueError('Tool must contain 1..200 finite edges')
    for edge in wire.Edges:
        if abs(edge.common(face).Length-edge.Length)>max(1e-7,edge.Length*1e-9):
            raise ValueError(tr('工具の全体を選択面の上に配置してください。自動投影・延長はありません。',
                                'Place the whole tool on the selected face. Projection and extension are not automatic.'))
    result=SplitAPI.slice(solid,[wire],'Standard')
    if result.isNull() or not result.isValid():raise ValueError('Native face split failed')
    checked_face_counts(len(solid.Faces),len(result.Faces),len(result.Solids))
    area_tol=max(1e-7,solid.Area*1e-9);volume_tol=max(1e-7,solid.Volume*1e-9)
    if (abs(result.Volume-solid.Volume)>volume_tol or abs(result.Area-solid.Area)>area_tol
            or result.cut(solid).Volume+solid.cut(result).Volume>volume_tol):
        raise ValueError('Face split changed the solid volume or boundary')
    pieces=[f for f in result.Faces if f.common(face).Area>=f.Area-max(1e-7,f.Area*1e-9)]
    if (len(pieces)<2 or len(result.Faces)-len(solid.Faces)!=len(pieces)-1
            or abs(sum(f.Area for f in pieces)-face.Area)>max(1e-7,face.Area*1e-9)):
        raise ValueError('The tool did not split only the selected face into complete regions')
    return result.Solids[0]
