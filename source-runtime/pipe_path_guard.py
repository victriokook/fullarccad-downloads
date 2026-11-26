"""Direct original pipe path checks and container dependencies."""
import FreeCAD as App
from model_defeature import containers

def checked(doc,path,existing=None):
    if path is None:return
    if path.Document!=doc or doc.getObject(path.Name)!=path or path.isDerivedFrom('App::Link'):raise ValueError('Select a live non-Link path in the current document.')
    if existing and (path==existing or existing in path.OutListRecursive):raise ValueError('Cyclic pipe path.')
    if any('Invalid' in o.State or 'Error' in o.State or bool(getattr(o,'Error','')) for o in [path]+list(path.OutListRecursive)):raise ValueError('Repair path source errors first.')

def stamp(path):
    return (tuple(o.Name for o in containers(path)),tuple((o.Name,tuple(o.State),str(getattr(o,'Error',''))) for o in [path]+list(path.OutListRecursive)))

def assign(obj,path):
    for typ,key in [('App::PropertyLinkListGlobal','PipePathContainers'),('App::PropertyStringList','PipePathHierarchy')]:
        if key not in obj.PropertiesList:obj.addProperty(typ,key,'FluxCAD');obj.setEditorMode(key,2)
    parents=containers(path) if path else []
    obj.PipePathContainers=parents;obj.PipePathHierarchy=[o.Name for o in parents]

def verify_hierarchy(obj,path):
    if 'PipePathHierarchy' in obj.PropertiesList and [o.Name for o in containers(path)]!=list(obj.PipePathHierarchy):raise ValueError('Path hierarchy changed; reselect the path.')

class HierarchyObserver:
    def __init__(self):self.previous={}
    def slotBeforeChangeObject(self,changed,prop):
        if prop=='Group' and changed.TypeId in ('App::Part','PartDesign::Body') and changed.Document:self.previous[(changed.Document.Name,changed.Name)]={o.Name for o in changed.Group}
    def slotChangedObject(self,changed,prop):
        if prop!='Group' or changed.TypeId not in ('App::Part','PartDesign::Body') or not changed.Document:return
        doc=changed.Document;members=self.previous.pop((doc.Name,changed.Name),set())|{o.Name for o in changed.Group}
        for obj in doc.Objects:
            if getattr(obj,'FluxPrimitive',None)=='pipe' and getattr(obj,'FluxPath',None):
                source=obj.FluxPath
                if source.Name in members or changed in containers(source) or changed in list(getattr(obj,'PipePathContainers',[])):obj.touch()
    def slotDeletedDocument(self,doc):self.previous={key:value for key,value in self.previous.items() if key[0]!=doc.Name}

def install_observer():
    old=getattr(App,'_flux_pipe_path_observer',None)
    if old is not None:App.removeDocumentObserver(old)
    observer=HierarchyObserver();App.addDocumentObserver(observer);App._flux_pipe_path_observer=observer
install_observer()
