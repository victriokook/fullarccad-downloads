"""Texture-preserving glTF importer for FullArcCAD's native mesh viewport."""
from pathlib import Path
from i18n import tr
import hashlib,json,math,tempfile,time
import numpy as np
import FreeCAD as App,FreeCADGui as Gui,Mesh,MeshGui
from PySide import QtCore,QtGui
from gltf_data import Asset

_runtime={};_temporary={};_players={};_guard=set();_observer=None
CONVERSION=np.array([[1000.,0,0,0],[0,0,-1000.,0],[0,1000.,0,0],[0,0,0,1]])

def key(root):return root.Document.Name,root.Name
def runtime(root):
    k=key(root)
    if k not in _runtime:_runtime[k]=Asset(str(root.SourceGLB))
    return _runtime[k]

def _matrix(values):
    m=App.Matrix()
    for i in range(4):
        for j in range(4):setattr(m,'A'+str(i+1)+str(j+1),float(values[i,j]))
    return m

def render_arrays(root,node_index,primitive_index):
    asset=runtime(root);data=asset.primitive(node_index,primitive_index)
    world=getattr(asset,'baked_world',{}).get((node_index,primitive_index),asset.base_world[node_index])
    transform=CONVERSION@world
    points=data['positions']@transform[:3,:3].T+transform[:3,3]
    normals=data['normals']@np.linalg.inv(transform[:3,:3])
    lengths=np.linalg.norm(normals,axis=1);normals/=np.where(lengths>1e-20,lengths,1)[:,None]
    faces=data['faces'].copy()
    if np.linalg.det(transform[:3,:3])<0:faces=faces[:,[0,2,1]]
    return points,normals,faces

def mesh_value(points,faces):
    return Mesh.Mesh(([App.Vector(float(p[0]),float(p[1]),float(p[2])) for p in points],[tuple(int(i) for i in face) for face in faces]))

def apply_pose(root):
    asset=runtime(root);index=int(root.AnimationIndex)
    worlds=asset.world_matrices(float(root.AnimationTime),index)
    if not hasattr(asset,'baked_world'):asset.baked_world={}
    for obj in root.Meshes:
        identity=(obj.NodeIndex,obj.PrimitiveIndex)
        delta=CONVERSION@worlds[obj.NodeIndex]@np.linalg.inv(asset.base_world[obj.NodeIndex])@np.linalg.inv(CONVERSION)
        rigid=np.allclose(delta[:3,:3].T@delta[:3,:3],np.eye(3),atol=1e-7) and np.linalg.det(delta[:3,:3])>0
        if rigid:
            if identity in asset.baked_world:
                asset.baked_world.pop(identity);points,normals,faces=render_arrays(root,*identity);obj.Mesh=mesh_value(points,faces);obj.ViewObject.Proxy.rebuild()
            placement=App.Placement(_matrix(delta))
            if not obj.Placement.isSame(placement,1e-10):obj.Placement=placement
        else:
            old=asset.baked_world.get(identity)
            if old is None or not np.allclose(old,worlds[obj.NodeIndex],atol=1e-12):
                asset.baked_world[identity]=worlds[obj.NodeIndex];points,normals,faces=render_arrays(root,*identity)
                obj.Mesh=mesh_value(points,faces);obj.Placement=App.Placement();obj.ViewObject.Proxy.rebuild()

def refresh_materials(root):
    asset=runtime(root)
    for obj in root.Meshes:
        index=asset.material_index(obj.NodeIndex,obj.PrimitiveIndex,int(root.VariantIndex))
        encoded=json.dumps(asset.material(index),separators=(',',':'))
        if obj.MaterialJSON!=encoded:obj.MaterialJSON=encoded
        elif obj.ViewObject.Proxy:obj.ViewObject.Proxy.rebuild()

def stop(root):
    player=_players.pop(key(root),None)
    if player:player.stop();player.deleteLater()

def play(root):
    stop(root)
    asset=runtime(root)
    if int(root.AnimationIndex)<0 or not asset.animations:return
    duration=asset.animations[int(root.AnimationIndex)]['duration']
    if duration<=0:return
    timer=QtCore.QTimer(Gui.getMainWindow());timer.setInterval(33);clock=[time.monotonic()]
    def tick():
        try:
            if App.ActiveDocument is not root.Document or not root.Play:
                root.Play=False;stop(root);return
            now=time.monotonic();dt=now-clock[0];clock[0]=now
            root.AnimationTime=(float(root.AnimationTime)+dt)%duration
        except (RuntimeError,ReferenceError):timer.stop()
        except Exception as error:
            App.Console.PrintError('glTF animation: '+str(error)+'\n');timer.stop()
    timer.timeout.connect(__import__('builtins')._fullarc_qt_slot(tick));_players[key(root)]=timer;timer.start()

class AssetProxy:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):pass
    def onChanged(self,obj,prop):
        if key(obj) in _guard or not getattr(obj,'SourceGLB','') or not getattr(obj,'Meshes',None):return
        _guard.add(key(obj))
        try:
            if prop=='MaterialVariant':
                obj.VariantIndex=list(obj.MaterialVariant).index(str(obj.MaterialVariant))-1 if isinstance(obj.MaterialVariant,list) else obj.getEnumerationsOfProperty('MaterialVariant').index(str(obj.MaterialVariant))-1
                refresh_materials(obj)
            elif prop=='Animation':
                obj.AnimationIndex=obj.getEnumerationsOfProperty('Animation').index(str(obj.Animation))-1;obj.AnimationTime=0.;apply_pose(obj)
            elif prop=='AnimationTime':apply_pose(obj)
            elif prop=='Play':play(obj) if obj.Play else stop(obj)
        finally:_guard.discard(key(obj))
    def onDocumentRestored(self,obj):
        _runtime.pop(key(obj),None)
        name,doc=obj.Name,obj.Document.Name
        def restored():
            try:
                root=App.getDocument(doc).getObject(name)
                if root is None:return
                _guard.add(key(root));root.Play=False;_guard.discard(key(root))
                for mesh in root.Meshes:
                    if mesh.ViewObject.Proxy:mesh.ViewObject.Proxy.rebuild()
                apply_pose(root)
            except Exception as e:App.Console.PrintError('glTF restore: '+str(e)+'\n')
        QtCore.QTimer.singleShot(0,__import__('builtins')._fullarc_qt_slot(restored))
    def dumps(self):return None
    def loads(self,state):pass

class AssetView:
    def __init__(self,vobj):vobj.Proxy=self
    def attach(self,vobj):self.Object=vobj.Object
    def getDisplayModes(self,vobj):return []
    def onChanged(self,*args):pass
    def updateData(self,*args):pass
    def doubleClicked(self,vobj):
        import gltf_controls;gltf_controls.show(vobj.Object);return True
    def dumps(self):return None
    def loads(self,state):pass

def _add(root,kind,name,value=None,group='glTF'):
    root.addProperty(kind,name,group)
    if value is not None:setattr(root,name,value)

def _create(asset,path,doc):
    from gltf_view import MeshProxy,ViewProvider
    # Decode and validate every primitive before changing the CAD document.
    entries=[]
    for node in asset.active_nodes:
        n=asset.document['nodes'][node]
        if 'mesh' in n:
            for primitive in range(len(asset.document['meshes'][n['mesh']]['primitives'])):
                data=asset.primitive(node,primitive);entries.append((node,primitive))
                for variant in range(-1,len(asset.variant_names)):
                    m=asset.material(asset.material_index(node,primitive,variant))
                    from gltf_shader import uv_parameters
                    for field in ('baseColorTexture','metallicRoughnessTexture'):
                        uv_parameters(m.get('pbrMetallicRoughness',{}).get(field,{}))
                    for field in ('normalTexture','occlusionTexture','emissiveTexture'):uv_parameters(m.get(field,{}))
    if not entries:raise ValueError('glTF scene has no triangle meshes')
    temp=tempfile.TemporaryDirectory(prefix='fullarccad-gltf-');folder=Path(temp.name)
    packed=asset.package();source=folder/'source.glb';source.write_bytes(packed)
    image_paths=[]
    for i,(data,mime) in enumerate(asset.images):
        image=QtGui.QImage.fromData(data)
        if image.isNull():temp.cleanup();raise ValueError('Cannot decode glTF image '+str(i))
        p=folder/('image'+str(i)+{'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[mime]);p.write_bytes(data);image_paths.append(p)
    controller=doc.addObject('App::FeaturePython','glTFAsset');controller.Label=Path(path).stem+tr(' — 表示設定', ' — Display Settings')
    _guard.add(key(controller));_temporary[key(controller)]=temp;_runtime[key(controller)]=asset
    AssetProxy(controller);AssetView(controller.ViewObject)
    _add(controller,'App::PropertyBool','IsGltfAsset',True)
    _add(controller,'App::PropertyFileIncluded','SourceGLB',str(source))
    _add(controller,'App::PropertyString','SourceSHA256',hashlib.sha256(packed).hexdigest())
    _add(controller,'App::PropertyString','OriginalSHA256',hashlib.sha256(asset.original).hexdigest())
    _add(controller,'App::PropertyString','SourceName',Path(path).name)
    _add(controller,'App::PropertyInteger','ImageCount',len(image_paths))
    for i,p in enumerate(image_paths):_add(controller,'App::PropertyFileIncluded','Image'+str(i),str(p),'Images')
    _add(controller,'App::PropertyEnumeration','MaterialVariant',['元の材質']+asset.variant_names,'表示')
    controller.MaterialVariant='元の材質';_add(controller,'App::PropertyInteger','VariantIndex',-1)
    names=[a['name'] for a in asset.animations]
    _add(controller,'App::PropertyEnumeration','Animation',['なし']+names,'表示')
    controller.Animation=names[0] if names else 'なし';_add(controller,'App::PropertyInteger','AnimationIndex',0 if names else -1)
    duration=max([a['duration'] for a in asset.animations]+[0.])
    _add(controller,'App::PropertyFloatConstraint','AnimationTime',(0.,0.,max(duration,.001),.001),'表示')
    _add(controller,'App::PropertyBool','Play',False,'表示')
    _add(controller,'App::PropertyLinkListHidden','Meshes',[])
    group=doc.addObject('App::Part','glTFScene');group.Label=Path(path).stem;_add(controller,'App::PropertyLinkHidden','Scene',group)
    groups={}
    for i in asset.active_nodes:
        node=asset.document['nodes'][i];part=doc.addObject('App::Part','glTFNode');part.Label=node.get('name','Node '+str(i))
        parent=asset.parents[i];(group if parent is None else groups[parent]).addObject(part);groups[i]=part
    meshes=[]
    for node,primitive in entries:
        obj=doc.addObject('Mesh::FeaturePython','glTFMesh');obj.Label=asset.document['nodes'][node].get('name','Mesh')
        if len(asset.document['meshes'][asset.document['nodes'][node]['mesh']]['primitives'])>1:obj.Label+=' / '+str(primitive+1)
        groups[node].addObject(obj);MeshProxy(obj)
        for kind,name,value in [('App::PropertyLinkGlobal','Asset',controller),('App::PropertyInteger','NodeIndex',node),('App::PropertyInteger','PrimitiveIndex',primitive),('App::PropertyString','MaterialJSON',json.dumps(asset.material(asset.material_index(node,primitive))))]:_add(obj,kind,name,value)
        points,normals,faces=render_arrays(controller,node,primitive);obj.Mesh=mesh_value(points,faces)
        ViewProvider(obj.ViewObject);obj.ViewObject.DisplayMode='glTF';meshes.append(obj)
        for name in ('Asset','NodeIndex','PrimitiveIndex','MaterialJSON'):obj.setEditorMode(name,1)
    controller.Meshes=meshes
    for name in ('SourceSHA256','OriginalSHA256','SourceName','ImageCount','Meshes','VariantIndex','AnimationIndex','IsGltfAsset','Scene','SourceGLB')+tuple('Image'+str(i) for i in range(len(image_paths))):controller.setEditorMode(name,1)
    _guard.discard(key(controller));doc.recompute();apply_pose(controller)
    return controller

def insert(filename,docname):
    asset=Asset(filename);doc=App.getDocument(docname)
    before={x.Name for x in doc.Objects};doc.openTransaction(tr('glTFを読み込み', 'Import glTF'))
    try:controller=_create(asset,filename,doc);doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        for obj in list(doc.Objects):
            if obj.Name not in before:doc.removeObject(obj.Name)
        raise
    _finish(controller);return controller

def open(filename):
    asset=Asset(filename);doc=App.newDocument('glTFModel');doc.Label=Path(filename).stem
    try:controller=_create(asset,filename,doc)
    except Exception:App.closeDocument(doc.Name);raise
    _finish(controller);return controller

def _finish(controller):
    App.setActiveDocument(controller.Document.Name);view=Gui.getDocument(controller.Document.Name).activeView()
    view.setAnimationEnabled(False);view.viewAxonometric()
    ws=getattr(Gui,'fluxcad_workspace',None)
    if ws:ws.fit()
    else:view.fitAll()
    try:
        import recent_files;recent_files.remember(str(runtime(controller).original_path))
    except (AttributeError,ImportError):pass
    import gltf_controls;gltf_controls.show(controller)

class Observer:
    def slotStartSaveDocument(self,doc,*args):
        for o in doc.Objects:
            if getattr(o,'IsGltfAsset',False) and o.Play:o.Play=False
    def slotDeletedDocument(self,doc):
        try:name=doc.Name
        except (RuntimeError,ReferenceError):return
        for k in [k for k in _runtime if k[0]==name]:
            _guard.discard(k)
            _runtime.pop(k,None);timer=_players.pop(k,None)
            if timer:timer.stop();timer.deleteLater()
            temp=_temporary.pop(k,None)
            if temp:temp.cleanup()

def install():
    global _observer
    # Load the installed view provider at application startup, before restoring
    # any saved Python features (FreeCAD's document-import allowlist).
    import gltf_view
    App.changeImportModule('glTF (*.gltf *.GLTF *.glb *.GLB)','ImportGui','gltf_import')
    if _observer is None:_observer=Observer();App.addDocumentObserver(_observer)
