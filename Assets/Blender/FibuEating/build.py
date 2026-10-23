"""Author a separate eating candidate: original skeleton, fitted face, facial morphs.
Run with Python + numpy/scipy/Pillow/usd-core. Never changes active app resources.
"""
from pathlib import Path
import json, math, zipfile, shutil, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from pxr import Usd, UsdGeom, UsdSkel, UsdShade, UsdUtils, Gf, Vt, Sdf
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]; OUT=ROOT/'generated'; OUT.mkdir(exist_ok=True)
SOURCE=OUT/'source'; SOURCE.mkdir(exist_ok=True)
assert hashlib.sha256((REPO/'Assets/Models/Fibu.Proportions.usdz').read_bytes()).hexdigest()=='819ef67d0d86d2572fd0fc1c4d0eca611d516c514e297225beb1e12d1ba7f4b5','Approved model changed: re-review face fitting and rig before rebuilding.'
with zipfile.ZipFile(REPO/'Assets/Models/Fibu.Proportions.usdz') as archive:
    for entry in archive.infolist():
        target=SOURCE/entry.filename
        assert target.resolve().is_relative_to(SOURCE.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(entry))
    rootname=archive.namelist()[0]
stage=Usd.Stage.Open(str(SOURCE/rootname));sk=next(UsdSkel.Skeleton(p) for p in stage.Traverse() if p.IsA(UsdSkel.Skeleton));body=next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh))
anim=next(UsdSkel.Animation(p) for p in stage.Traverse() if p.IsA(UsdSkel.Animation))
def queries():
    c=UsdSkel.Cache()
    for p in stage.Traverse():
        if p.IsA(UsdSkel.Root):c.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    return c,c.GetSkelQuery(sk)
cache,q=queries();baseT,baseR,baseS=UsdSkel.DecomposeTransforms(q.ComputeJointLocalTransforms(0));global0=q.ComputeJointSkelTransforms(0)
names=list(sk.GetJointsAttr().Get());ids={n.split('/')[-1]:i for i,n in enumerate(names)};parents=list(UsdSkel.Topology(names).GetParentIndices())
rest=np.array(body.GetPointsAttr().Get(),dtype=float);rawfaces=list(body.GetFaceVertexIndicesAttr().Get());rawuv=np.array(UsdGeom.PrimvarsAPI(body).GetPrimvar('st').ComputeFlattened())
triangles=[];triangleuv=[];cursor=0
for count in body.GetFaceVertexCountsAttr().Get():
    for i in range(1,count-1):
        corners=[cursor,cursor+i,cursor+i+1];triangles.append([rawfaces[k] for k in corners]);triangleuv.append([rawuv[k] for k in corners])
    cursor+=count
faces=np.array(triangles);uv=np.array(triangleuv)
bodybind=UsdSkel.BindingAPI(body);K=bodybind.GetJointIndicesPrimvar().GetElementSize();bindindices=np.array(bodybind.GetJointIndicesPrimvar().Get()).reshape(-1,K);bindweights=np.array(bodybind.GetJointWeightsPrimvar().Get()).reshape(-1,K)
def skinpoints(mesh,points,time=0):
    c,qq=queries();sq=c.GetSkinningQuery(mesh.GetPrim());points=Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in points]);assert sq.ComputeSkinnedPoints(qq.ComputeSkinningTransforms(time),points,time);return np.array(points,dtype=float)
pose=skinpoints(body,rest);floor=pose[:,2].min();height=np.ptp(pose[:,2]);unit=height/2.7

def uvpoint(target):
    for f,u in zip(faces,uv):
        a=np.stack([u[1]-u[0],u[2]-u[0]],axis=1)
        if abs(np.linalg.det(a))<1e-10:continue
        b=np.linalg.solve(a,np.array(target)-u[0]);w=np.array([1-b.sum(),*b])
        if w.min()>-1e-5:return np.sum(pose[f]*w[:,None],axis=0)
    raise ValueError('UV outside surface')
mouth=uvpoint((.620,.623));print('Mouth normalized',mouth/unit,'height',(mouth[2]-floor)/unit,flush=True)
# Generate a narrowly targeted smile mask from the original texture. Artist originals survive.
texdir=SOURCE/'EatingTextures';texdir.mkdir(exist_ok=True)
original=Image.open(SOURCE/'0/Feeb_skin.png').convert('RGB');a=np.array(original);yy,xx=np.indices(a.shape[:2]);region=(xx>a.shape[1]*.57)&(xx<a.shape[1]*.68)&(yy>a.shape[0]*.33)&(yy<a.shape[0]*.43)
mask=(a[:,:,0]<150)&(a[:,:,1]<115)&(a[:,:,2]<115)&region
mask=ndimage.binary_dilation(mask,iterations=7)
assert 100<mask.sum()<20000
skinrecords=[]
skins=[('Original',SOURCE/'0/Feeb_skin.png')]+[(p.stem.split('.')[0],p) for p in sorted((REPO/'Assets/Skins/Source').glob('*.texture.png'))]
artist=np.array(Image.open(REPO/'Assets/Skins/Source/000.texture.png').convert('RGB'))
ay,ax=np.indices(artist.shape[:2]);artistmask=(artist[:,:,0]<100)&(artist[:,:,1]<100)&(artist[:,:,2]<100)&(ax>artist.shape[1]*.55)&(ax<artist.shape[1]*.66)&(ay>artist.shape[0]*.34)&(ay<artist.shape[0]*.43)
artistmask=ndimage.binary_dilation(artistmask,iterations=9)
for label,path in skins:
    im=Image.open(path).convert('RGB');arr=np.array(im)
    template=mask if label=='Original' else artistmask
    m=np.array(Image.fromarray(template.astype('uint8')*255).resize(im.size,Image.Resampling.NEAREST))>0
    if label=='013':
        y,x=np.indices(arr.shape[:2]);m=((x/arr.shape[1]-.6055)/.043)**2+((y/arr.shape[0]-.373)/.034)**2<1
    ys,xs=np.where(m);y0,y1=max(0,ys.min()-16),min(arr.shape[0],ys.max()+17);x0,x1=max(0,xs.min()-16),min(arr.shape[1],xs.max()+17)
    cropmask=m[y0:y1,x0:x1];work=arr[y0:y1,x0:x1].astype(float)
    if label=='013':
        # Exemplar patch repair retains fur spots instead of diffusing them into a blank blob.
        border=ndimage.binary_dilation(cropmask,iterations=5)&~cropmask;best=None
        for dy in range(-256,257,16):
            for dx in range(-256,257,16):
                if abs(dx)<(x1-x0) and abs(dy)<(y1-y0):continue
                ya,yb,xa,xb=y0+dy,y1+dy,x0+dx,x1+dx
                if min(ya,xa)<0 or yb>arr.shape[0] or xb>arr.shape[1]:continue
                donor=arr[ya:yb,xa:xb].astype(float);score=np.abs(donor[border]-work[border]).mean()
                if best is None or score<best[0]:best=(score,donor.copy(),[dx,dy])
        assert best is not None
        alpha=np.minimum(1,ndimage.distance_transform_edt(cropmask)/6)[:,:,None];work=work*(1-alpha)+best[1]*alpha
    else:
        work[cropmask]=np.median(work[ndimage.binary_dilation(cropmask,iterations=5)&~cropmask],axis=0)
        for _ in range(220):
            avg=ndimage.uniform_filter(work,size=(3,3,1),mode='nearest');work[cropmask]=avg[cropmask]
    result=arr.copy();result[y0:y1,x0:x1]=np.clip(work,0,255).astype('uint8');assert np.array_equal(result[~m],arr[~m])
    filename=f'Skin.{label}.NoSmile.png';maskfile=f'Mask.{label}.png';Image.fromarray(result).save(texdir/filename);Image.fromarray(m.astype('uint8')*255).save(texdir/maskfile)
    skinrecords.append({'id':label,'source':('Assets/Models/Fibu.Proportions.usdz!0/Feeb_skin.png' if label=='Original' else str(path.relative_to(REPO))),'file':'EatingTextures/'+filename,'mask':'EatingTextures/'+maskfile,'changed_pixels':int(m.sum()),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'repair':'local exemplar fur patch; artist review required' if label=='013' else 'local diffusion of individually registered painted smile'})
# Only this separate candidate's embedded skin points to the cleaned derivative.
for p in stage.Traverse():
    if p.IsA(UsdShade.Shader):
        shader=UsdShade.Shader(p);inp=shader.GetInput('file')
        if inp and inp.Get() and 'Feeb_skin' in str(inp.Get()):inp.Set(Sdf.AssetPath('EatingTextures/Skin.Original.NoSmile.png'))
# Antialiased transparent expression art. Coordinates deliberately share a single face patch.
ink=(63,44,41,255);pink=(242,124,154,255)
def expression(name):
    im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im)
    def line(points,width=25):d.line([(int(x*2),int(y*2)) for x,y in points],fill=ink,width=width,joint='curve')
    def curve(points,width=25):
        p=np.array(points);ts=np.linspace(0,1,100);v=[(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3] for t in ts];line(v,width)
    def ellipse(box,fill,outline=None,width=12):d.ellipse(tuple(int(x*2) for x in box),fill=fill,outline=outline,width=width*2)
    if name=='smile':
        curve([(126,274),(208,302),(305,281),(365,236)]);curve([(353,221),(357,235),(365,246),(381,253)],18)
    elif name=='open':
        ellipse((176,143,347,341),ink);ellipse((200,170,322,315),pink);ellipse((219,166,320,238),ink)
    elif name=='lick':
        curve([(121,285),(209,312),(309,293),(367,265)])
        ellipse((257,180,365,299),ink);ellipse((273,193,349,288),pink);curve([(312,211),(306,228),(300,252),(299,272)],16)
    elif name=='chew':
        curve([(184,241),(220,199),(263,220),(274,258)])
        curve([(274,258),(262,299),(222,303),(195,280)])
    elif name=='swallow':
        curve([(229,207),(178,202),(174,245),(221,253)])
        curve([(221,253),(176,260),(186,300),(236,294)])
    elif name=='happy':
        poly=[(135,234),(196,258),(271,260),(366,222),(340,306),(289,337),(223,338),(165,303)]
        d.polygon([(x*2,y*2) for x,y in poly],fill=ink);ellipse((211,287,318,325),pink)
    im.resize((512,512),Image.Resampling.LANCZOS).save(texdir/f'Mouth.{name}.png')
expressions=['smile','open','lick','chew','swallow','happy']
for name in expressions:expression(name)
# Project a rectangular UV grid onto the front-facing body triangles at the neutral pose.
# Each overlay point retains triangle+barycentric anchors for the local renderer.
N=17;width=.67*unit;patchheight=.61*unit
xz=pose[faces][:,:,[0,2]];A=np.stack([xz[:,1]-xz[:,0],xz[:,2]-xz[:,0]],axis=2);valid=abs(np.linalg.det(A))>1e-9;inv=np.zeros_like(A);inv[valid]=np.linalg.inv(A[valid])
anchors=[];surface=[];overlayuv=[]
for j in range(N):
    for i in range(N):
        u=i/(N-1);v=j/(N-1);target=mouth[[0,2]]+np.array([(u-.5)*width,(v-.5)*patchheight])
        b=np.einsum('fij,fj->fi',inv,target-xz[:,0]);w=np.column_stack([1-b.sum(axis=1),b]);hits=valid&(w.min(axis=1)>-1e-5);candidates=np.where(hits)[0];assert len(candidates)
        points=np.einsum('fi,fij->fj',w[candidates],pose[faces[candidates]]);pick=int(np.argmin(points[:,1]));face=int(candidates[pick]);point=points[pick];point[1]-=.0035*unit
        anchors.append({'triangle':face,'vertexIndices':faces[face].tolist(),'barycentric':w[face].tolist()});surface.append(point);overlayuv.append([u,v])
surface=np.array(surface);ofaces=[]
for j in range(N-1):
    for i in range(N-1):
        a=j*N+i;ofaces.extend([[a,a+1,a+N],[a+1,a+N+1,a+N]])
# Joint weights interpolated from the same body triangles, preserving its motion.
oindices=[];oweights=[]
for anchor in anchors:
    weights={}
    for vertex,b in zip(faces[anchor['triangle']],anchor['barycentric']):
        for k,w in zip(bindindices[vertex],bindweights[vertex]):weights[int(k)]=weights.get(int(k),0)+w*b
    top=sorted(weights.items(),key=lambda x:-x[1])[:10];total=sum(w for _,w in top);oindices.append([i for i,_ in top]+[0]*(10-len(top)));oweights.append([w/total for _,w in top]+[0]*(10-len(top)))
parent=body.GetPath().GetParentPath();facepaths=[]
def bindmesh(mesh,indices,weights):
    binding=UsdSkel.BindingAPI.Apply(mesh.GetPrim());binding.CreateSkeletonRel().SetTargets([sk.GetPath()]);binding.CreateGeomBindTransformAttr(bodybind.GetGeomBindTransformAttr().Get());binding.CreateJointsAttr(names)
    binding.CreateJointIndicesPrimvar(False,10).Set(Vt.IntArray(np.array(indices).ravel().tolist()));binding.CreateJointWeightsPrimvar(False,10).Set(Vt.FloatArray(np.array(weights).ravel().tolist()))
# Invert the exact per-point LBS mapping at the neutral pose. No guessed coordinate transform.
def inversemap(mesh,count):
    zero=np.zeros((count,3));origin=skinpoints(mesh,zero);columns=[]
    for axis in range(3):
        p=zero.copy();p[:,axis]=1;columns.append(skinpoints(mesh,p)-origin)
    jac=np.stack(columns,axis=2);return origin,np.linalg.inv(jac)
origin,bodyinv=inversemap(body,len(rest))
# Cheek morph changes the silhouette locally; no belly collapse or bone scaling.
center=mouth.copy();center[0]-=.43*unit;center[1]+=.20*unit;center[2]-=.03*unit
norm=(pose-center)/unit
weight=np.exp(-((norm[:,0]/.30)**2+(norm[:,1]/.60)**2+(norm[:,2]/.25)**2))
cheek=np.column_stack([-.17*unit*weight,-.12*unit*weight,.018*unit*weight])
snorm=(pose-(mouth+np.array([0,0,-.23*unit])))/unit
sw=np.exp(-((snorm[:,0]/.27)**2+(snorm[:,1]/.30)**2+(snorm[:,2]/.16)**2))
swallow=np.column_stack([np.zeros(len(rest)),-.035*unit*sw,-.035*unit*sw])
bodyoffsets=[np.einsum('nij,nj->ni',bodyinv,delta) for delta in [cheek,swallow]]
def smoothnormals(points,triangles):
    normals=np.zeros_like(points);triangles=np.array(triangles);p=points[triangles];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    for i in range(3):np.add.at(normals,triangles[:,i],cross)
    return normals/np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
def blendshapes(mesh,offsets):
    binding=UsdSkel.BindingAPI.Apply(mesh.GetPrim());paths=[]
    points=np.array(mesh.GetPointsAttr().Get());tri=faces if mesh.GetPath()==body.GetPath() else np.array(ofaces);normals=smoothnormals(points,tri);mesh.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in normals]));mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    for name,offset in zip(['CheekPuff','Swallow'],offsets):
        shape=UsdSkel.BlendShape.Define(stage,mesh.GetPath().AppendChild(name));shape.CreateOffsetsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in offset]));shape.CreateNormalOffsetsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in smoothnormals(points+offset,tri)-normals]));paths.append(shape.GetPath())
    binding.CreateBlendShapesAttr(['CheekPuff','Swallow']);binding.CreateBlendShapeTargetsRel().SetTargets(paths)
blendshapes(body,bodyoffsets)
# Smooth vertex normals and morph normal offsets accompany the facial surface changes.
meshes=[]
for name in expressions:
    mesh=UsdGeom.Mesh.Define(stage,parent.AppendChild('Face_'+name));mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(0) for _ in surface]));mesh.CreateFaceVertexCountsAttr([3]*len(ofaces));mesh.CreateFaceVertexIndicesAttr(np.array(ofaces).ravel().tolist());mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateDoubleSidedAttr(False)
    bindmesh(mesh,oindices,oweights);ori,invj=inversemap(mesh,len(surface));raw=np.einsum('nij,nj->ni',invj,surface-ori);mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in raw]))
    blend=[]
    for delta in [cheek,swallow]:
        interpolated=np.array([np.sum(delta[faces[a['triangle']]]*np.array(a['barycentric'])[:,None],axis=0) for a in anchors]);blend.append(np.einsum('nij,nj->ni',invj,interpolated))
    blendshapes(mesh,blend)
    st=UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,UsdGeom.Tokens.vertex);st.Set(Vt.Vec2fArray([Gf.Vec2f(*v) for v in overlayuv]))
    mat=UsdShade.Material.Define(stage,parent.AppendChild('MouthMaterial_'+name));shader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Surface'));shader.CreateIdAttr('UsdPreviewSurface');shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.9);shader.CreateInput('opacityThreshold',Sdf.ValueTypeNames.Float).Set(.05)
    tex=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Texture'));tex.CreateIdAttr('UsdUVTexture');tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(f'EatingTextures/Mouth.{name}.png'));tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
    reader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('UV'));reader.CreateIdAttr('UsdPrimvarReader_float2');reader.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st');tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(),'result');shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),'rgb');shader.CreateInput('opacity',Sdf.ValueTypeNames.Float).ConnectToSource(tex.ConnectableAPI(),'a');mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface');UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    mesh.CreateVisibilityAttr().Set(UsdGeom.Tokens.inherited if name=='smile' else UsdGeom.Tokens.invisible)
    meshes.append((name,mesh,raw,blend));facepaths.append(str(mesh.GetPath()))
# CCD hand reach, applied to the original USD joint rotations, with small bounded steps.
def globals_for(rot):
    result=[]
    for i,m in enumerate(UsdSkel.MakeTransforms(baseT,rot,baseS)):result.append(m if parents[i]<0 else m*result[parents[i]])
    return result
def reach(target):
    rot=Vt.QuatfArray(baseR)
    for _ in range(45):
        for joint in ['Forearm_R','Bicep_R','Shoulder_R']:
            g=globals_for(rot);i=ids[joint];o=g[i].ExtractTranslation();end=g[ids['Hand_R_end']].ExtractTranslation();a=np.array(end-o);b=np.array(target)-np.array(o);a/=np.linalg.norm(a);b/=np.linalg.norm(b);axis=np.cross(a,b);length=np.linalg.norm(axis)
            if length<1e-7:continue
            axis/=length;angle=min(9,math.degrees(math.acos(float(np.clip(a@b,-1,1)))));P=Gf.Matrix4d(1).SetRotate(g[parents[i]].ExtractRotation());L=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Quatd(rot[i])));D=Gf.Matrix4d(1).SetRotate(Gf.Rotation(Gf.Vec3d(*axis),angle));qq=(L*P*D*P.GetInverse()).ExtractRotationQuat();qq.Normalize();rot[i]=Gf.Quatf(qq)
    return rot
bitepose=reach(mouth+np.array([-.08,-.22,-.13])*unit)
cheerpose=reach(mouth+np.array([-.90,.30,.32])*unit)
def smooth(t):t=np.clip(t,0,1);return float(t*t*(3-2*t))
def envelope(t,start,peak,hold,end):return smooth((t-start)/(peak-start))*(1-smooth((t-hold)/(end-hold)))
def expression_at(t):
    for start,end,name in [(0,.22,'smile'),(.22,.96,'open'),(.96,1.48,'lick'),(1.48,1.68,'open'),(1.68,2.02,'chew'),(2.02,2.18,'swallow'),(2.18,2.62,'happy'),(2.62,2.8,'smile')]:
        if start<=t<end:return name
    return 'smile'
FPS=30;duration=2.8;frames=round(FPS*duration)
anim.GetTranslationsAttr().Clear();anim.GetRotationsAttr().Clear();anim.GetScalesAttr().Clear();anim.GetJointsAttr().Set(names);anim.CreateBlendShapesAttr(['CheekPuff','Swallow']);stage.SetTimeCodesPerSecond(FPS);stage.SetFramesPerSecond(FPS);stage.SetStartTimeCode(0);stage.SetEndTimeCode(frames)
anim.GetTranslationsAttr().Set(baseT);anim.GetRotationsAttr().Set(baseR);anim.GetScalesAttr().Set(baseS);anim.CreateBlendShapeWeightsAttr().Set(Vt.FloatArray([0,0]))
timeline=[]
for frame in range(frames+1):
    t=frame/FPS;amount=envelope(t,.18,.78,1.0,1.46);rot=Vt.QuatfArray(baseR)
    for joint in ['Shoulder_R','Bicep_R','Forearm_R','Hand_R']:
        i=ids[joint];rot[i]=Gf.Slerp(amount,baseR[i],bitepose[i]);rot[i]=Gf.Slerp(envelope(t,.96,1.42,2.35,2.72),rot[i],cheerpose[i])
    # Mild neck anticipation, no whole-body squash or leg motion.
    i=ids['Neck'];nod=-3.0*envelope(t,.18,.75,1.15,1.55)+2.0*envelope(t,2.05,2.2,2.3,2.55);rot[i]=Gf.Quatf(Gf.Rotation(Gf.Vec3d(1,0,0),nod).GetQuat())*rot[i]
    puff=envelope(t,1.55,1.76,1.89,2.10);swallowweight=envelope(t,1.96,2.12,2.16,2.33)
    anim.GetTranslationsAttr().Set(baseT,frame);anim.GetRotationsAttr().Set(rot,frame);anim.GetScalesAttr().Set(baseS,frame);anim.CreateBlendShapeWeightsAttr().Set(Vt.FloatArray([puff,swallowweight]),frame)
    expr=expression_at(t)
    for name,mesh,_,_ in meshes:mesh.CreateVisibilityAttr().Set(UsdGeom.Tokens.inherited if name==expr else UsdGeom.Tokens.invisible,frame)
    timeline.append({'handReach':amount,'frame':frame,'time':t,'expression':expr,'cheekPuff':puff,'swallow':swallowweight,'foodVisible':t<.96,'biteEvent':frame==29})
# Evaluate EVERY sample; include morphs explicitly before LBS for preview/validation.
previews=[];mins=[];finite=True
for row in timeline:
    f=row['frame'];weights=np.array([row['cheekPuff'],row['swallow']]);deformed=rest+sum((off*w for off,w in zip(bodyoffsets,weights)),np.zeros_like(rest));points=skinpoints(body,deformed,f)
    c,qq=queries();g=qq.ComputeJointSkelTransforms(f);hand=np.array(g[ids['Hand_R_end']].ExtractTranslation());mins.append(float(points[:,2].min()));assert np.isfinite(points).all();assert np.ptp(points,axis=0).max()<height*1.2
    facepoints=skinpoints(meshes[0][1],meshes[0][2]+sum((off*w for off,w in zip(meshes[0][3],weights)),np.zeros_like(surface)),f)
    # Fit against the ACTUAL animated surface. Renderer can use these barycentric anchors too.
    anchored=np.array([np.sum(points[faces[a['triangle']]]*np.array(a['barycentric'])[:,None],axis=0) for a in anchors]);errors=np.linalg.norm(facepoints-(anchored+np.array([0,-.0035*unit,0])),axis=1)
    foodposition=hand+np.array([-.05*(1-row['handReach']),-.42*(1-row['handReach'])-.055*row['handReach'],.12])*unit
    row['foodPositionSkeletonSpace']=foodposition.tolist();row['foodPositionHandLocal']=list(g[ids['Hand_R_end']].GetInverse().Transform(Gf.Vec3d(*foodposition)))
    previews.append({'food':foodposition.tolist(),'frame':f,'body':points.tolist(),'face':facepoints.tolist(),'hand':hand.tolist(),'expression':row['expression'],'foodVisible':row['foodVisible'],'maxFaceFitError':float(errors.max())})
assert max(abs(v-floor) for v in mins)<.003
# A replaceable, independent bread placeholder. App code can hide it and attach real food.
prop=UsdGeom.Xform.Define(stage,parent.AppendChild('PreviewFood'));translation=prop.AddTranslateOp();scaleop=prop.AddScaleOp();translation.Set(Gf.Vec3d(*timeline[0]['foodPositionSkeletonSpace']));scaleop.Set(Gf.Vec3f(1))
for row in timeline:
    translation.Set(Gf.Vec3d(*row['foodPositionSkeletonSpace']),row['frame']);scaleop.Set(Gf.Vec3f(1 if row['foodVisible'] else 0),row['frame'])
bread=UsdGeom.Mesh.Define(stage,prop.GetPath().AppendChild('Bread'));vertices=[];breadfaces=[];segments=24;rings=12
for j in range(rings+1):
    theta=math.pi*j/rings
    for i in range(segments):
        phi=math.tau*i/segments;vertices.append([.145*unit*math.sin(theta)*math.cos(phi),.09*unit*math.sin(theta)*math.sin(phi),.105*unit*math.cos(theta)])
for j in range(rings):
    for i in range(segments):
        a=j*segments+i;b=j*segments+(i+1)%segments;breadfaces.extend([[a,a+segments,b],[b,a+segments,b+segments]])
bread.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in vertices]));bread.CreateFaceVertexCountsAttr([3]*len(breadfaces));bread.CreateFaceVertexIndicesAttr(np.array(breadfaces).ravel().tolist());bread.CreateSubdivisionSchemeAttr('none');bread.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float,v)) for v in smoothnormals(np.array(vertices),breadfaces)]));bread.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
mat=UsdShade.Material.Define(stage,prop.GetPath().AppendChild('GoldenBread'));shader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Surface'));shader.CreateIdAttr('UsdPreviewSurface');shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.66,.23,.035));shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.8);mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface');UsdShade.MaterialBindingAPI.Apply(bread.GetPrim()).Bind(mat)
# Standalone export: the currently active app and approved model stay byte-for-byte untouched.
layer=SOURCE/'Fibu.Eat.usdc';stage.GetRootLayer().Export(str(layer));package=OUT/'Fibu.Eat.usdz';assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(layer)),str(package));assert Usd.Stage.Open(str(package));assert not UsdUtils.ComputeAllDependencies(str(package))[2]
(OUT/'preview-data.json').write_text(json.dumps({'fps':FPS,'duration':duration,'floor':float(floor),'unit':float(unit),'faces':faces.tolist(),'uv':uv.reshape(-1,2).tolist(),'overlayFaces':ofaces,'overlayUV':overlayuv,'frames':previews}))
(OUT/'face-anchors.json').write_text(json.dumps({'schemaVersion':1,'bodyVertexCount':len(rest),'overlayGrid':[N,N],'offsetInPreviewUnits':.0035,'anchors':anchors},indent=2))
(OUT/'timeline.json').write_text(json.dumps({'schemaVersion':1,'fps':FPS,'duration':duration,'loop':False,'foodJoint':'Hand_R_end','foodBiteTime':29/FPS,'mouthVisibility':'exclusive expression nodes; do not crossfade dark artwork','samples':timeline},indent=2))
(OUT/'skins.json').write_text(json.dumps({'schemaVersion':1,'skins':skinrecords,'note':'Automatic smile removal is a review derivative. Patterned skins need artist inspection; never overwrite originals.'},indent=2))
report={'bodyVertices':len(rest),'bodyTriangles':len(faces),'joints':len(names),'samples':len(previews),'duration':duration,'floorMaxError':max(abs(v-floor) for v in mins),'maxFaceFitError':max(p['maxFaceFitError'] for p in previews)/unit,'skinDerivatives':len(skinrecords),'packageDependenciesResolved':True,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'limitations':['No SceneKit/Xcode execution in cloud.','USD face visibility and blendshape playback require native loader verification; timeline included for explicit control.','Artist review needed for automatic smile removal, especially patterned skins.','Food prop is a separate preview placeholder; no app feeding/rewards integration.']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
