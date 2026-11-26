"""glTF material shading for the existing Coin/OpenGL viewport."""
VERTEX = r'''#version 120
varying vec3 P; varying vec3 N; varying vec2 UV0; varying vec2 UV1;
void main(){vec4 p=gl_ModelViewMatrix*gl_Vertex;P=p.xyz;N=normalize(gl_NormalMatrix*gl_Normal);
UV0=gl_MultiTexCoord0.st;UV1=gl_MultiTexCoord1.st;gl_Position=gl_ProjectionMatrix*p;}
'''
FRAGMENT = r'''#version 120
varying vec3 P;varying vec3 N;varying vec2 UV0;varying vec2 UV1;
uniform sampler2D baseMap,normalMap,ormMap,aoMap,emissiveMap;
uniform int hasBase,hasNormal,hasORM,hasAO,hasEmissive,unlit,alphaMode;
uniform vec4 baseFactor;uniform vec3 emissiveFactor;
uniform float metallic,roughness,normalScale,aoStrength,transmission,alphaCutoff,ior;
uniform vec4 uvBase,uvNormal,uvORM,uvAO,uvEmissive;
uniform vec2 rotBase,rotNormal,rotORM,rotAO,rotEmissive;
vec2 texuv(vec4 t,vec2 r){vec2 p=(r.y>0.5?UV1:UV0)*t.zw;float c=cos(r.x),s=sin(r.x);
p=mat2(c,s,-s,c)*p+t.xy;return vec2(p.x,1.0-p.y);}
vec3 env(vec3 r){float h=clamp(r.y*.5+.5,0.0,1.0);vec3 c=mix(vec3(.10,.13,.18),vec3(.85,.89,.98),h);
float panel=pow(max(0.0,dot(r,normalize(vec3(-.5,.6,.7)))),50.0);return c+vec3(panel*1.8);}
vec3 brdf(vec3 n,vec3 v,vec3 l,vec3 color,float m,float rough){
vec3 h=normalize(v+l);float nl=max(dot(n,l),0.0),nv=max(dot(n,v),.001),nh=max(dot(n,h),0.0),vh=max(dot(v,h),0.0);
float a=rough*rough,a2=a*a;float den=nh*nh*(a2-1.0)+1.0;float D=a2/(3.14159265*den*den);
float k=(rough+1.0)*(rough+1.0)/8.0;float G=(nv/(nv*(1.0-k)+k))*(nl/(nl*(1.0-k)+k));
float f0=pow((ior-1.0)/(ior+1.0),2.0);vec3 F0=mix(vec3(f0),color,m);vec3 F=F0+(1.0-F0)*pow(1.0-vh,5.0);
vec3 spec=D*G*F/max(4.0*nv*nl,.001);vec3 diff=(1.0-F)*(1.0-m)*color/3.14159265;
return (diff*(1.0-transmission)+spec)*nl;}
void main(){
vec4 c=baseFactor;if(hasBase==1){vec4 t=texture2D(baseMap,texuv(uvBase,rotBase));c*=vec4(pow(max(t.rgb,vec3(0.0)),vec3(2.2)),t.a);}
float alpha=alphaMode==0?1.0:c.a;if(alphaMode==1 && c.a<alphaCutoff)discard;
float m=metallic,r=roughness;if(hasORM==1){vec4 q=texture2D(ormMap,texuv(uvORM,rotORM));m*=q.b;r*=q.g;}r=clamp(r,.045,1.0);m=clamp(m,0.0,1.0);
vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;
if(hasNormal==1){vec2 uv=texuv(uvNormal,rotNormal);vec3 map=texture2D(normalMap,uv).xyz*2.0-1.0;map.xy*=normalScale;map.y=-map.y;
vec3 dx=dFdx(P),dy=dFdy(P);vec2 tx=dFdx(uv),ty=dFdy(uv);vec3 T=dx*ty.y-dy*tx.y;vec3 B=-dx*ty.x+dy*tx.x;
float det=tx.x*ty.y-tx.y*ty.x;T*=sign(det);B*=sign(det);if(length(T)>.000001&&length(B)>.000001)n=normalize(mat3(normalize(T),normalize(B),n)*map);}
float ao=1.0;if(hasAO==1)ao=mix(1.0,texture2D(aoMap,texuv(uvAO,rotAO)).r,aoStrength);
vec3 emission=emissiveFactor;if(hasEmissive==1)emission*=pow(texture2D(emissiveMap,texuv(uvEmissive,rotEmissive)).rgb,vec3(2.2));
vec3 v=normalize(-P),f0=mix(vec3(.04),c.rgb,m);float fres=pow(1.0-max(dot(n,v),0.0),5.0);
vec3 ambient=c.rgb*(1.0-m)*.32*(1.0-transmission)*ao;
vec3 reflection=env(reflect(-v,n))*mix(f0,vec3(1.0),fres)*mix(.8,.18,r)*ao;
vec3 color=ambient+reflection+emission;
color+=brdf(n,v,normalize(vec3(.4,.65,1.0)),c.rgb,m,r)*vec3(2.8);
color+=brdf(n,v,normalize(vec3(-.7,.3,.5)),c.rgb,m,r)*vec3(.8,.85,1.0);
if(unlit==1)color=c.rgb+emission;
// Thin transmission is displayed by compositing; full refraction is retained
// in the source material but the CAD viewport has no scene refraction buffer.
if(transmission>0.0)alpha*=max(.08,1.0-transmission);
color=color/(color+vec3(1.0));gl_FragColor=vec4(pow(max(color,vec3(0.0)),vec3(1.0/2.2)),alpha);
}
'''

def uv_parameters(info):
    transform=info.get('extensions',{}).get('KHR_texture_transform',{})
    offset=transform.get('offset',(0.,0.));scale=transform.get('scale',(1.,1.));channel=transform.get('texCoord',info.get('texCoord',0))
    if channel not in (0,1):raise ValueError('Only glTF UV sets 0 and 1 are supported')
    return (*offset,*scale),(transform.get('rotation',0.),float(channel))
