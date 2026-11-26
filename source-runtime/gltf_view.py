"""Saved Python mesh view provider retaining UV, material images and PBR data."""
from i18n import tr
from pathlib import Path
import json
import numpy as np
import FreeCAD as App,FreeCADGui as Gui
from pivy import coin
from gltf_shader import VERTEX,FRAGMENT,uv_parameters

def parameter(kind,name,value):
    p=kind();p.name=name;p.value=value;return p

def shader(material,root):
    program=coin.SoShaderProgram();vertex=coin.SoVertexShader();fragment=coin.SoFragmentShader()
    vertex.sourceType=coin.SoShaderObject.GLSL_PROGRAM;fragment.sourceType=coin.SoShaderObject.GLSL_PROGRAM
    vertex.sourceProgram=VERTEX;fragment.sourceProgram=FRAGMENT
    pbr=material.get('pbrMetallicRoughness',{});extensions=material.get('extensions',{})
    transmission=extensions.get('KHR_materials_transmission',{}).get('transmissionFactor',0.)
    emission=material.get('emissiveFactor',(0.,0.,0.));strength=extensions.get('KHR_materials_emissive_strength',{}).get('emissiveStrength',1.)
    params=[parameter(coin.SoShaderParameter4f,'baseFactor',tuple(pbr.get('baseColorFactor',(1.,1.,1.,1.)))),
            parameter(coin.SoShaderParameter3f,'emissiveFactor',tuple(v*strength for v in emission))]
    numbers={'metallic':pbr.get('metallicFactor',1.),'roughness':pbr.get('roughnessFactor',1.),'normalScale':material.get('normalTexture',{}).get('scale',1.),
             'aoStrength':material.get('occlusionTexture',{}).get('strength',1.),'transmission':transmission,'alphaCutoff':material.get('alphaCutoff',.5),
             'ior':extensions.get('KHR_materials_ior',{}).get('ior',1.5)}
    for name,value in numbers.items():params.append(parameter(coin.SoShaderParameter1f,name,float(value)))
    for name,value in [('unlit',int('KHR_materials_unlit' in extensions)),('alphaMode',{'OPAQUE':0,'MASK':1,'BLEND':2}.get(material.get('alphaMode','OPAQUE'),0))]:params.append(parameter(coin.SoShaderParameter1i,name,value))
    maps=[('baseMap','hasBase','uvBase','rotBase',pbr.get('baseColorTexture',{})),('normalMap','hasNormal','uvNormal','rotNormal',material.get('normalTexture',{})),
          ('ormMap','hasORM','uvORM','rotORM',pbr.get('metallicRoughnessTexture',{})),('aoMap','hasAO','uvAO','rotAO',material.get('occlusionTexture',{})),
          ('emissiveMap','hasEmissive','uvEmissive','rotEmissive',material.get('emissiveTexture',{}))]
    from gltf_import import runtime
    asset=runtime(root)
    textures=[]
    for unit,(name,flag,uv_name,rot_name,info) in enumerate(maps):
        params.extend([parameter(coin.SoShaderParameter1i,name,unit),parameter(coin.SoShaderParameter1i,flag,int('index' in info))])
        uv,rot=uv_parameters(info);params.extend([parameter(coin.SoShaderParameter4f,uv_name,uv),parameter(coin.SoShaderParameter2f,rot_name,rot)])
        selector=coin.SoTextureUnit();selector.unit=unit;textures.append(selector)
        texture=coin.SoTexture2()
        if 'index' in info:
            tex=asset.document['textures'][info['index']];image_index=tex['source'];path=str(getattr(root,'Image'+str(image_index)))
            if not Path(path).is_file():raise ValueError('Saved glTF image is missing')
            texture.filename=path
            sampler=asset.document.get('samplers',[])[tex['sampler']] if 'sampler' in tex else {}
            texture.wrapS=coin.SoTexture2.CLAMP if sampler.get('wrapS',10497)==33071 else coin.SoTexture2.REPEAT
            texture.wrapT=coin.SoTexture2.CLAMP if sampler.get('wrapT',10497)==33071 else coin.SoTexture2.REPEAT
        textures.append(texture)
    fragment.parameter.setValues(0,len(params),params)
    program.shaderObject.setValues(0,2,[vertex,fragment])
    return program,textures,float(transmission)

class MeshProxy:
    def __init__(self,obj):obj.Proxy=self
    def execute(self,obj):pass
    def dumps(self):return None
    def loads(self,state):pass

class ViewProvider:
    def __init__(self,vobj):vobj.Proxy=self
    def attach(self,vobj):
        self.Object=vobj.Object;self.node=coin.SoSeparator();self._building=False
        vobj.addDisplayMode(self.node,'glTF');self.rebuild()
    def getDisplayModes(self,vobj):return ['glTF']
    def getDefaultDisplayMode(self):return 'glTF'
    def setDisplayMode(self,mode):return mode
    def updateData(self,obj,prop):
        if prop in ('Asset','NodeIndex','PrimitiveIndex','MaterialJSON'):self.rebuild()
    def onChanged(self,vobj,prop):pass
    def rebuild(self):
        if self._building:return
        obj=self.Object
        if not getattr(obj,'Asset',None) or not getattr(obj.Asset,'SourceGLB',''):return
        self._building=True
        try:
            from gltf_import import runtime,render_arrays
            asset=runtime(obj.Asset);data=asset.primitive(obj.NodeIndex,obj.PrimitiveIndex)
            points,normals,faces=render_arrays(obj.Asset,obj.NodeIndex,obj.PrimitiveIndex)
            index=asset.material_index(obj.NodeIndex,obj.PrimitiveIndex,int(obj.Asset.VariantIndex))
            material=asset.material(index);program,textures,transmission=shader(material,obj.Asset)
            group=coin.SoSeparator();mat=coin.SoMaterial();base=material.get('pbrMetallicRoughness',{}).get('baseColorFactor',(1,1,1,1))
            mat.diffuseColor=tuple(base[:3]);mat.transparency=max(1-base[3],.92*transmission) if material.get('alphaMode')=='BLEND' or transmission else 0.;group.addChild(mat)
            if hasattr(coin,'SoTransparencyType'):
                transparency=coin.SoTransparencyType();transparency.value=coin.SoGLRenderAction.SORTED_OBJECT_BLEND;group.addChild(transparency)
            hints=coin.SoShapeHints();hints.vertexOrdering=coin.SoShapeHints.COUNTERCLOCKWISE
            hints.shapeType=coin.SoShapeHints.UNKNOWN_SHAPE_TYPE if material.get('doubleSided',False) else coin.SoShapeHints.SOLID
            group.addChild(hints)
            for texture in textures:group.addChild(texture)
            # Each set is independent of texture unit selection for sampling.
            for channel in (0,1):
                unit=coin.SoTextureUnit();unit.unit=channel;group.addChild(unit)
                uv=coin.SoTextureCoordinate2();uv.point.setValues(0,len(data['uv'][channel]),data['uv'][channel].tolist());group.addChild(uv)
            group.addChild(program)
            coords=coin.SoCoordinate3();coords.point.setValues(0,len(points),points.tolist());group.addChild(coords)
            n=coin.SoNormal();n.vector.setValues(0,len(normals),normals.tolist());group.addChild(n)
            bind=coin.SoNormalBinding();bind.value=coin.SoNormalBinding.PER_VERTEX_INDEXED;group.addChild(bind)
            shape=coin.SoIndexedFaceSet();indices=np.column_stack((faces,np.full(len(faces),-1,dtype=int))).ravel().tolist()
            shape.coordIndex.setValues(0,len(indices),indices);shape.normalIndex.setValues(0,len(indices),indices);shape.textureCoordIndex.setValues(0,len(indices),indices)
            group.addChild(shape);self.node.removeAllChildren();self.node.addChild(group)
        finally:self._building=False
    def getElementPicked(self,picked):
        detail=picked.getDetail()
        return 'Facet'+str(detail.getFaceIndex()+1) if isinstance(detail,coin.SoFaceDetail) else ''
    def setupContextMenu(self,vobj,menu):
        action=menu.addAction(tr('glTF 表示設定…'))
        action.triggered[bool].connect(__import__('builtins')._fullarc_qt_slot(lambda:__import__('gltf_controls').show(vobj.Object.Asset),(0, 0, False, False)))
    def dumps(self):return None
    def loads(self,state):pass
