"""One-way angular ratio between independent root FullArcCAD revolute joints."""
import FreeCAD as App
import model,model_assembly as assembly
from motion_link_values import linked_angle

def links(doc):return [x for x in doc.Objects if getattr(x,'FluxMotionLink',False)]
def used(joint):return any(x.Driver==joint or x.DrivenName==joint.Name for x in links(joint.Document))
def driven(link):return link.Document.getObject(link.DrivenName)
def guard_joint(joint):
    name=getattr(joint,'MotionLinkName','')
    if not name:return
    obj=joint.Document.getObject(name)
    if obj and getattr(obj,'FluxLinearMotionLink',False):
        from linear_motion_link import guard_joint as guard_linear
        return guard_linear(joint)
    if not obj or not getattr(obj,'FluxMotionLink',False) or obj.DrivenName!=joint.Name or not obj.Valid or str(joint.Kind)!='revolute' or not obj.Driver or str(obj.Driver.Kind)!='revolute' or dict(joint.ExpressionEngine).get('Angle')!=obj.Name+'.OutputAngle':raise ValueError('Repair or release the rotational motion link')
def checked(driver,follower,existing=None,executing=False):
    if driver is None or follower is None or driver==follower or driver.Document!=follower.Document:raise ValueError('Select two different same-document revolute joints')
    doc=driver.Document
    if existing and (existing.Document!=doc or not getattr(existing,'FluxMotionLink',False) or existing.Driver!=driver or existing.DrivenName!=follower.Name):raise ValueError('Motion-link endpoints cannot change;release and recreate')
    for joint in (driver,follower):
        if doc.getObject(joint.Name)!=joint or not getattr(joint,'FluxJoint',False) or str(joint.Kind)!='revolute' or joint.getParentGeoFeatureGroup():raise ValueError('Initial scope:root FullArcCAD revolute joints only')
    if follower in driver.OutListRecursive or (existing and existing in driver.OutListRecursive):raise ValueError('Cyclic motion link')
    for link in links(doc):
        if link!=existing and any(j in (link.Driver,driven(link)) for j in (driver,follower)):raise ValueError('One motion link per joint;no chains')
    if not driver.Valid or driver.AssemblyError:raise ValueError('Repair the driving joint')
    if not executing:
        assembly.valid_component(assembly.follower_of(driver))
        if existing:assembly.local_shape(assembly.follower_of(follower).Source)
        else:assembly.valid_component(assembly.follower_of(follower))
    expression=dict(follower.ExpressionEngine).get('Angle')
    if expression and (not existing or expression!=existing.Name+'.OutputAngle'):raise ValueError('Driven Angle already has an expression')
    if getattr(driver,'MotionLinkName',''):raise ValueError('Motion link chains are unsupported')
    return doc
def settings(obj):return dict(one=float(obj.ValueOne),two=float(obj.ValueTwo),reverse=bool(obj.Reverse))
def stamp(driver,follower,existing=None):
    checked(driver,follower,existing)
    return (tuple((x.Name,tuple(assembly.settings(x).items()),x.Valid,x.AssemblyError,tuple(x.ExpressionEngine),str(x.Target.getGlobalPlacement())) for x in (driver,follower)),None if not existing else (tuple(settings(existing).items()),existing.DriverZero,existing.DrivenZero,existing.Valid,existing.Error))
class MotionLink:
    def execute(self,obj):
        try:
            follower=driven(obj);checked(obj.Driver,follower,obj,True)
            if getattr(follower,'MotionLinkName','')!=obj.Name or dict(follower.ExpressionEngine).get('Angle')!=obj.Name+'.OutputAngle':raise ValueError('Driven angle expression changed')
            value=linked_angle(obj.Driver.Angle.Value,obj.DriverZero,obj.DrivenZero,obj.ValueOne,obj.ValueTwo,obj.Reverse)
            if follower.Limited and not follower.Minimum.Value<=value<=follower.Maximum.Value:raise ValueError('Linked angle exceeds driven joint limits')
            obj.OutputAngle=value;obj.Valid=True;obj.Error=''
        except Exception as error:obj.Valid=False;obj.Error=str(error)
    def dumps(self):return None
    def loads(self,state):pass
def apply(driver,follower,one=360.,two=360.,reverse=False,existing=None,expected=None):
    doc=checked(driver,follower,existing)
    if expected is not None and stamp(driver,follower,existing)!=expected:raise ValueError('Inputs changed;close and reopen')
    zero1=existing.DriverZero if existing else driver.Angle.Value;zero2=existing.DrivenZero if existing else follower.Angle.Value
    value=linked_angle(driver.Angle.Value,zero1,zero2,one,two,reverse)
    if follower.Limited and not follower.Minimum.Value<=value<=follower.Maximum.Value:raise ValueError('Linked angle exceeds driven joint limits')
    part=assembly.follower_of(follower);values=assembly.settings(follower);values['angle']=value
    predicted=assembly.affected_poses(doc,{part:assembly.pose(follower.Target.getGlobalPlacement(),follower.Relative,**values)})
    consumers={x.Name:(x,tuple(bool(getattr(x.Shape,n)) for n in ('Solids','Faces','Edges'))) for comp in predicted for x in comp.InListRecursive if hasattr(x,'Shape')}
    with model.transaction(doc,'Rotational Motion Link'):
        obj=existing
        if obj is None:
            obj=doc.addObject('App::FeaturePython','MotionLink');obj.Proxy=MotionLink();obj.ViewObject.Proxy=0
            for typ,key in [('App::PropertyBool','FluxMotionLink'),('App::PropertyLink','Driver'),('App::PropertyString','DrivenName'),('App::PropertyFloat','ValueOne'),('App::PropertyFloat','ValueTwo'),('App::PropertyBool','Reverse'),('App::PropertyFloat','DriverZero'),('App::PropertyFloat','DrivenZero'),('App::PropertyAngle','OutputAngle'),('App::PropertyBool','Valid'),('App::PropertyString','Error')]:obj.addProperty(typ,key,'MotionLink')
            obj.FluxMotionLink=True;obj.Driver=driver;obj.DrivenName=follower.Name;obj.DriverZero=zero1;obj.DrivenZero=zero2;obj.Label='Rotational Motion Link'
            for key in ('FluxMotionLink','Driver','DrivenName','DriverZero','DrivenZero'):obj.setEditorMode(key,2)
            for key in ('OutputAngle','Valid','Error'):obj.setEditorMode(key,1)
            if 'MotionLinkName' not in follower.PropertiesList:follower.addProperty('App::PropertyString','MotionLinkName','MotionLink')
            follower.setEditorMode('MotionLinkName',2);follower.MotionLinkName=obj.Name;obj.OutputAngle=value;obj.Valid=True;follower.setExpression('Angle',obj.Name+'.OutputAngle')
        obj.ValueOne=one;obj.ValueTwo=two;obj.Reverse=reverse;obj.touch();doc.recompute()
        if not obj.Valid:raise ValueError(obj.Error)
        assembly.verify(predicted)
        for child,dimensions in consumers.values():
            if 'Invalid' in child.State or getattr(child,'Error','') or getattr(child,'AssemblyError','') or child.Shape.isNull() or not child.Shape.isValid() or any(was and not bool(getattr(child.Shape,n)) for n,was in zip(('Solids','Faces','Edges'),dimensions)):raise ValueError('Later geometry would disappear;motion-link edit cancelled')
    return obj
def release(obj):
    follower=driven(obj)
    if not follower or not obj.Valid:raise ValueError('Repair the link before releasing')
    angle=follower.Angle.Value;pose=App.Placement(assembly.follower_of(follower).Placement)
    with model.transaction(obj.Document,'Release Motion Link'):
        follower.setExpression('Angle',None);follower.Angle=angle;follower.MotionLinkName='';doc=obj.Document;doc.removeObject(obj.Name);doc.recompute();assembly.verify({assembly.follower_of(follower):pose})

class DeletionObserver:
    def slotDeletedObject(self,obj):
        if not getattr(obj,'FluxMotionLink',False) or getattr(obj,'FluxLinearMotionLink',False) or not obj.Document:return
        follower=driven(obj)
        if follower and getattr(follower,'MotionLinkName','')==obj.Name:
            # Remove the dangling native expression before it can prevent execute.
            # Keep the ownership marker so normal Joint.execute fails closed.
            follower.setExpression('Angle',None);follower.Valid=False;follower.AssemblyError='Motion link deleted;Undo to restore';follower.touch()
            part=assembly.follower_of(follower)
            if part:part.touch()
old=getattr(App,'_fullarc_motion_link_observer',None)
if old is not None:App.removeDocumentObserver(old)
App._fullarc_motion_link_observer=DeletionObserver();App.addDocumentObserver(App._fullarc_motion_link_observer)
