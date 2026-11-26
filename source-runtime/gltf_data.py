"""Local glTF 2 data, retained independently of CAD tessellation/healing."""
import base64, copy, hashlib, json, math, mimetypes, struct
from pathlib import Path
from urllib.parse import unquote
import numpy as np
from gltf_math import read_accessor, sample_animation

SUPPORTED_EXTENSIONS = {'KHR_materials_transmission', 'KHR_materials_variants', 'KHR_texture_transform', 'KHR_materials_unlit', 'KHR_materials_emissive_strength', 'KHR_materials_ior'}

def local_resource(uri, folder):
    if uri.startswith('data:'):
        head, payload = uri.split(',', 1)
        if ';base64' not in head: raise ValueError('Only base64 data resources are supported')
        return base64.b64decode(payload, validate=True)
    if ':' in uri or uri.startswith(('/', '\\')): raise ValueError('glTF resources must be local relative files')
    path = (folder / unquote(uri)).resolve()
    if not path.is_relative_to(folder.resolve()): raise ValueError('glTF resource is outside its folder')
    return path.read_bytes()

def parse_file(path):
    path = Path(path); raw = path.read_bytes(); binary = None
    if raw[:4] == b'glTF':
        if len(raw) < 20: raise ValueError('Truncated GLB')
        magic, version, total = struct.unpack_from('<4sII', raw)
        if version != 2 or total != len(raw): raise ValueError('Invalid GLB header')
        offset = 12; document = None
        while offset < total:
            if offset + 8 > total: raise ValueError('Truncated GLB chunk')
            length, kind = struct.unpack_from('<II', raw, offset); offset += 8
            if length % 4 or offset + length > total: raise ValueError('Invalid GLB chunk')
            chunk = raw[offset:offset+length]; offset += length
            if kind == 0x4e4f534a:
                if document is not None: raise ValueError('Duplicate GLB JSON chunk')
                document = json.loads(chunk.rstrip(b' \x00'))
            elif kind == 0x004e4942:
                if binary is not None: raise ValueError('Duplicate GLB binary chunk')
                binary = chunk
        if document is None: raise ValueError('GLB has no JSON')
    else: document = json.loads(raw.decode('utf-8-sig'))
    if document.get('asset', {}).get('version') != '2.0': raise ValueError('Only glTF 2.0 is supported')
    unsupported = set(document.get('extensionsRequired', [])) - SUPPORTED_EXTENSIONS
    if unsupported: raise ValueError('Unsupported required glTF extensions: '+', '.join(sorted(unsupported)))
    buffers=[]
    for i, info in enumerate(document.get('buffers', [])):
        data = local_resource(info['uri'], path.parent) if 'uri' in info else binary if i == 0 else None
        if data is None or len(data) < info['byteLength']: raise ValueError('Missing or truncated glTF buffer')
        buffers.append(data[:info['byteLength']])
    for view in document.get('bufferViews', []):
        if 'EXT_meshopt_compression' in view.get('extensions', {}): raise ValueError('Use an uncompressed glTF/GLB')
        b= buffers[view['buffer']]; start=view.get('byteOffset',0); length=view['byteLength']
        if start<0 or length<0 or start+length>len(b): raise ValueError('glTF buffer view is out of range')
    images=[]
    for info in document.get('images', []):
        if 'uri' in info: data=local_resource(info['uri'],path.parent)
        else:
            v=document['bufferViews'][info['bufferView']];start=v.get('byteOffset',0);data=buffers[v['buffer']][start:start+v['byteLength']]
        if data.startswith(b'\x89PNG'): mime='image/png'
        elif data.startswith(b'\xff\xd8'): mime='image/jpeg'
        elif data[:4]==b'RIFF' and data[8:12]==b'WEBP': mime='image/webp'
        else: raise ValueError('Use PNG, JPEG or WebP textures for the CAD viewport')
        images.append((data,mime))
    return document,buffers,images,raw

def packed_glb(document,buffers,images):
    g=copy.deepcopy(document);blob=bytearray();bases=[]
    for data in buffers:
        blob.extend(b'\x00'*(-len(blob)%4));bases.append(len(blob));blob.extend(data)
    for v in g.get('bufferViews',[]):
        v['byteOffset']=v.get('byteOffset',0)+bases[v['buffer']];v['buffer']=0
    for info,(data,mime) in zip(g.get('images',[]),images):
        if 'uri' in info:
            blob.extend(b'\x00'*(-len(blob)%4));index=len(g.setdefault('bufferViews',[]))
            g['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(data)});blob.extend(data)
            info.pop('uri');info['bufferView']=index
        info['mimeType']=mime
    g['buffers']=[{'byteLength':len(blob)}]
    encoded=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*(-len(encoded)%4);blob.extend(b'\x00'*(-len(blob)%4))
    return struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(blob))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(blob),0x004e4942)+blob

def rotation_matrix(q):
    x,y,z,w=map(float,q);norm=math.sqrt(x*x+y*y+z*z+w*w)
    if norm<1e-12: raise ValueError('Invalid glTF quaternion')
    x,y,z,w=(v/norm for v in (x,y,z,w))
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)], [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)], [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

class Asset:
    def __init__(self,path):
        self.original_path=Path(path)
        self.document,self.buffers,self.images,self.original=parse_file(path)
        self._accessors={};self._primitives={}
        self.variant_names=[x.get('name',str(i)) for i,x in enumerate(self.document.get('extensions',{}).get('KHR_materials_variants',{}).get('variants',[]))]
        self.active_nodes=[];self.parents={};seen=set();active=set()
        scenes=self.document.get('scenes',[{'nodes':list(range(len(self.document.get('nodes',[]))))}])
        roots=scenes[self.document.get('scene',0)].get('nodes',[])
        def visit(index,parent):
            if index in active or index in seen: raise ValueError('Cyclic or multiply-parented glTF node')
            node=self.document['nodes'][index]
            if 'skin' in node: raise ValueError('Skinned glTF meshes are not supported by this importer')
            active.add(index);seen.add(index);self.parents[index]=parent;self.active_nodes.append(index)
            for child in node.get('children',[]):visit(child,index)
            active.remove(index)
        for index in roots:visit(index,None)
        self.animations=[]
        for animation in self.document.get('animations',[]):
            channels=[];duration=0.
            for channel in animation.get('channels',[]):
                sampler=animation['samplers'][channel['sampler']];times=self.accessor(sampler['input']);values=self.accessor(sampler['output'])
                if channel['target']['path'] not in ('translation','rotation','scale'): raise ValueError('Morph animation is not supported')
                if times:duration=max(duration,max(times))
                channels.append((channel['target']['node'],channel['target']['path'],times,values,sampler.get('interpolation','LINEAR')))
            self.animations.append({'name':animation.get('name','Animation '+str(len(self.animations)+1)),'duration':duration,'channels':channels})
        self.base_world=self.world_matrices(0,0)

    def accessor(self,index):
        if index not in self._accessors:self._accessors[index]=read_accessor(self.document,self.buffers,index)
        return self._accessors[index]

    def world_matrices(self,time_value=0.,animation_index=0):
        overrides={}
        if self.animations and animation_index>=0:
            for node,path,times,values,interpolation in self.animations[animation_index]['channels']:
                overrides[node,path]=sample_animation(times,values,float(time_value),interpolation,path=='rotation')
        result={}
        for index in self.active_nodes:
            node=self.document['nodes'][index]
            if 'matrix' in node:
                local=np.array(node['matrix'],dtype=float).reshape((4,4),order='F')
                if any((index,p) in overrides for p in ('translation','rotation','scale')): raise ValueError('Animation cannot target a matrix node')
            else:
                t=overrides.get((index,'translation'),node.get('translation',(0,0,0)))
                q=overrides.get((index,'rotation'),node.get('rotation',(0,0,0,1)))
                scale=overrides.get((index,'scale'),node.get('scale',(1,1,1)))
                local=np.eye(4);local[:3,:3]=rotation_matrix(q)@np.diag(scale);local[:3,3]=t
            if not np.isfinite(local).all() or abs(np.linalg.det(local[:3,:3]))<1e-14:raise ValueError('Nonfinite or singular glTF transform')
            parent=self.parents[index];result[index]=local if parent is None else result[parent]@local
        return result

    def primitive(self,node_index,primitive_index):
        key=node_index,primitive_index
        if key in self._primitives:return self._primitives[key]
        node=self.document['nodes'][node_index];mesh=self.document['meshes'][node['mesh']];p=mesh['primitives'][primitive_index]
        if p.get('targets') or 'KHR_draco_mesh_compression' in p.get('extensions',{}):raise ValueError('Use an uncompressed, non-morph glTF mesh')
        positions=np.array(self.accessor(p['attributes']['POSITION']),dtype=float)
        if positions.ndim!=2 or positions.shape[1]!=3 or not np.isfinite(positions).all():raise ValueError('Invalid glTF positions')
        indices=list(self.accessor(p['indices'])) if 'indices' in p else list(range(len(positions)))
        if any(type(i) is not int or i<0 or i>=len(positions) for i in indices):raise ValueError('Invalid glTF indices')
        mode=p.get('mode',4)
        if mode==4:
            if len(indices)%3:raise ValueError('Incomplete glTF triangles')
            faces=np.array(indices,dtype=int).reshape((-1,3))
        elif mode==5:faces=np.array([(indices[i],indices[i+1],indices[i+2]) if i%2==0 else (indices[i+1],indices[i],indices[i+2]) for i in range(len(indices)-2)],dtype=int)
        elif mode==6:faces=np.array([(indices[0],indices[i],indices[i+1]) for i in range(1,len(indices)-1)],dtype=int)
        else:raise ValueError('Only triangle glTF primitives are supported')
        if 'NORMAL' in p['attributes']:normals=np.array(self.accessor(p['attributes']['NORMAL']),dtype=float)
        else:
            normals=np.zeros_like(positions);cross=np.cross(positions[faces[:,1]]-positions[faces[:,0]],positions[faces[:,2]]-positions[faces[:,0]])
            for column in range(3):np.add.at(normals,faces[:,column],cross)
        if normals.shape!=positions.shape:raise ValueError('Invalid glTF normals')
        lengths=np.linalg.norm(normals,axis=1);normals/=np.where(lengths>1e-20,lengths,1)[:,None]
        uv=[]
        for channel in (0,1):
            values=np.array(self.accessor(p['attributes']['TEXCOORD_'+str(channel)]),dtype=float) if 'TEXCOORD_'+str(channel) in p['attributes'] else np.zeros((len(positions),2))
            if values.shape!=(len(positions),2) or not np.isfinite(values).all():raise ValueError('Invalid glTF UV coordinates')
            uv.append(values)
        data={'positions':positions,'normals':normals,'faces':faces,'uv':uv,'primitive':p,'material':p.get('material',-1)}
        self._primitives[key]=data;return data

    def material_index(self,node_index,primitive_index,variant=-1):
        p=self.primitive(node_index,primitive_index)['primitive']
        if variant>=0:
            for mapping in p.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
                if variant in mapping['variants']:return mapping['material']
        return p.get('material',-1)

    def material(self,index):
        return self.document.get('materials',[])[index] if index>=0 else {}

    def package(self):return packed_glb(self.document,self.buffers,self.images)
