"""Reviewed local-Qwen accessor and animation proposals, with format guards."""
import bisect, math, struct

def _integer(value, name):
    if type(value) is not int or value<0:raise ValueError('Invalid glTF '+name)
    return value

def read_accessor(gltf,buffers,index):
    try:
        _integer(index,'accessor index');a=gltf['accessors'][index]
        formats={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
        dimensions={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
        fmt,size=formats[a['componentType']];width=dimensions[a['type']];count=_integer(a['count'],'accessor count')
        if count>50_000_000:raise ValueError('glTF accessor is too large')
        normalized=a.get('normalized',False)
        if normalized and a['componentType'] not in (5120,5121,5122,5123):raise ValueError('Invalid normalized glTF component type')
        unpack=struct.Struct('<'+fmt*width)
        def values(view_index,offset,n,reader,stride=None):
            _integer(view_index,'buffer view');v=gltf['bufferViews'][view_index]
            bi=_integer(v['buffer'],'buffer index');data=buffers[bi]
            start=_integer(v.get('byteOffset',0),'buffer offset');length=_integer(v['byteLength'],'buffer length')
            offset=_integer(offset,'accessor offset');stride=v.get('byteStride',reader.size) if stride is None else stride
            if type(stride) is not int or stride<reader.size or start+length>len(data):raise ValueError('Invalid glTF stride or view')
            end=offset+(n-1)*stride+reader.size if n else offset
            if end>length:raise ValueError('glTF accessor exceeds its buffer view')
            return [reader.unpack_from(data,start+offset+i*stride) for i in range(n)]
        raw=values(a['bufferView'],a.get('byteOffset',0),count,unpack) if 'bufferView' in a else [tuple(0 for _ in range(width)) for _ in range(count)]
        if 'sparse' in a:
            sparse=a['sparse'];n=_integer(sparse['count'],'sparse count')
            if n>count:raise ValueError('Invalid sparse glTF count')
            indices=sparse['indices'];kind=indices['componentType']
            if kind not in (5121,5123,5125):raise ValueError('Invalid sparse index component')
            index_reader=struct.Struct('<'+formats[kind][0])
            patches=values(indices['bufferView'],indices.get('byteOffset',0),n,index_reader,index_reader.size)
            val=sparse['values'];replacement=values(val['bufferView'],val.get('byteOffset',0),n,unpack,unpack.size)
            previous=-1
            for (target,),value in zip(patches,replacement):
                if target<=previous or target>=count:raise ValueError('Invalid sparse glTF index')
                raw[target]=value;previous=target
        result=[]
        for vector in raw:
            if normalized:
                if a['componentType']==5120:vector=tuple(max(-1.,v/127.) for v in vector)
                elif a['componentType']==5121:vector=tuple(v/255. for v in vector)
                elif a['componentType']==5122:vector=tuple(max(-1.,v/32767.) for v in vector)
                else:vector=tuple(v/65535. for v in vector)
            if not all(math.isfinite(x) for x in vector):raise ValueError('Nonfinite glTF accessor')
            result.append(vector[0] if width==1 else tuple(vector))
        return result
    except (KeyError,IndexError,TypeError,struct.error,OverflowError) as e:raise ValueError('Invalid glTF accessor: '+str(e)) from None

def _quaternion(q):
    length=math.sqrt(sum(v*v for v in q))
    if length<1e-15:raise ValueError('Zero animation quaternion')
    return tuple(v/length for v in q)

def sample_animation(times,values,time_value,interpolation,quaternion=False):
    if not times or interpolation not in ('STEP','LINEAR','CUBICSPLINE'):raise ValueError('Invalid glTF animation')
    if any(not math.isfinite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:])) or not math.isfinite(time_value):raise ValueError('Invalid animation times')
    cubic=interpolation=='CUBICSPLINE'
    if len(values)!=len(times)*(3 if cubic else 1):raise ValueError('Invalid animation output length')
    width=len(values[0])
    if not width or any(len(v)!=width or not all(math.isfinite(x) for x in v) for v in values) or (quaternion and width!=4):raise ValueError('Invalid animation values')
    def value(index):return tuple(values[3*index+1] if cubic else values[index])
    if time_value<=times[0]:result=value(0)
    elif time_value>=times[-1]:result=value(len(times)-1)
    else:
        i=bisect.bisect_right(times,time_value)-1;dt=times[i+1]-times[i];t=(time_value-times[i])/dt
        a=value(i);b=value(i+1)
        if interpolation=='STEP':result=a
        elif cubic:
            h00=2*t**3-3*t*t+1;h10=t**3-2*t*t+t;h01=-2*t**3+3*t*t;h11=t**3-t*t
            result=tuple(h00*a[k]+h10*dt*values[3*i+2][k]+h01*b[k]+h11*dt*values[3*(i+1)][k] for k in range(width))
        elif quaternion:
            a=_quaternion(a);b=_quaternion(b);dot=sum(x*y for x,y in zip(a,b))
            if dot<0:b=tuple(-x for x in b);dot=-dot
            dot=max(-1.,min(1.,dot))
            if dot>.9995:result=tuple(x+t*(y-x) for x,y in zip(a,b))
            else:
                angle=math.acos(dot);den=math.sin(angle);wa=math.sin((1-t)*angle)/den;wb=math.sin(t*angle)/den
                result=tuple(wa*x+wb*y for x,y in zip(a,b))
        else:result=tuple(x+t*(y-x) for x,y in zip(a,b))
    return _quaternion(result) if quaternion else tuple(result)
