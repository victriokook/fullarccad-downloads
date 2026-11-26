"""Single-face trimming kernel candidate; face/shell tool, no auto extension."""
import FreeCAD as App
import Part
from BOPTools.SplitAPI import slice as slice_shape
from trim_selection import kept_indices

def pieces(source,tool,frame=None):
    if source.isNull() or not source.isValid() or source.ShapeType!='Face' or len(source.Faces)!=1:
        raise ValueError('Trim target must be one valid face')
    if tool.isNull() or not tool.isValid() or tool.ShapeType not in ('Face','Shell') or tool.Solids:
        raise ValueError('Trim tool must be a whole valid face or shell')
    result=slice_shape(source.copy(),[tool.copy()],'Split')
    faces=result.Faces
    if not 2<=len(faces)<=200 or any(not f.isValid() or f.Area<=1e-9 for f in faces):
        raise ValueError('Tool must split the face into2–200 regions')
    tolerance=max(1e-7,source.Area*1e-7)
    if abs(sum(f.Area for f in faces)-source.Area)>tolerance or any(f.common(source).Area<f.Area-tolerance for f in faces):
        raise ValueError('Split regions do not preserve the original surface')
    inverse=(frame if frame is not None else App.Placement()).inverse()
    metrics=[]
    for face in faces:
        center=inverse.multVec(face.CenterOfMass);metrics.append((center.x,center.y,center.z,face.Area))
    # Tiny equal-coordinate noise must not override a distinct next coordinate
    # (e.g. the two cylinder halves both have X=0 but opposite Y).
    tolerances=[max(1e-8,source.BoundBox.DiagonalLength*1e-9)]*3+[max(1e-8,source.Area*1e-9)]
    ranks=[]
    for axis,tol in enumerate(tolerances):
        order=sorted(range(len(faces)),key=__import__('builtins')._fullarc_qt_slot(lambda i:metrics[i][axis],(1, 1, False, False)));rank={};group=0
        anchor=previous=metrics[order[0]][axis]
        for index in order:
            value=metrics[index][axis]
            if value-anchor>tol:
                if value-previous<=4*tol:raise ValueError('Region ordering is numerically ambiguous; change the tool')
                group+=1;anchor=value
            rank[index]=group;previous=value
        ranks.append(rank)
    keys=[tuple(rank[i] for rank in ranks) for i in range(len(faces))]
    if len(set(keys))!=len(keys):raise ValueError('Regions have indistinguishable centers and areas; change the tool')
    return [faces[i] for i in sorted(range(len(faces)),key=__import__('builtins')._fullarc_qt_slot(lambda i:keys[i],(1, 1, False, False)))]

def trimmed(regions,keep):
    indices=kept_indices(keep,len(regions));selected=[regions[i] for i in indices]
    result=selected[0].copy() if len(selected)==1 else Part.makeCompound([f.copy() for f in selected])
    if result.isNull() or not result.isValid() or result.Solids or len(result.Faces)!=len(selected):
        raise ValueError('Invalid trimmed surface')
    return result
