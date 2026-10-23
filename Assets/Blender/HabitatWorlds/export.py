"""Package painted modules and complete habitats, sharing materials within each scene."""
from pathlib import Path
import json,shutil,hashlib
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf,Gf,Vt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'generated'
def material(stage,path,d):
    m=UsdShade.Material.Define(stage,path);bs=UsdShade.Shader.Define(stage,path+'/Surface');bs.CreateIdAttr('UsdPreviewSurface')
    bs.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*d.get('color',[.5,.5,.5])))
    bs.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(d.get('roughness',.86))
    bs.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(0)
    if any(d.get('emission',[0,0,0])):bs.CreateInput('emissiveColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*d['emission']))
    uv=UsdShade.Shader.Define(stage,path+'/UV');uv.CreateIdAttr('UsdPrimvarReader_float2');uv.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st');uv.CreateOutput('result',Sdf.ValueTypeNames.Float2)
    for kind,filename in d.get('textures',{}).items():
        shutil.copy2(ROOT/'textures'/filename,OUT/filename)
        tex=UsdShade.Shader.Define(stage,path+'/'+kind);tex.CreateIdAttr('UsdUVTexture');tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(filename));tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB' if kind=='color' else 'raw')
        for axis in ['S','T']:tex.CreateInput('wrap'+axis,Sdf.ValueTypeNames.Token).Set('repeat')
        tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(uv.ConnectableAPI(),'result')
        if kind=='normal':
            tex.CreateInput('scale',Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(.9,.9,2,1));tex.CreateInput('bias',Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(-.45,-.45,-1,0))
            tex.CreateOutput('rgb',Sdf.ValueTypeNames.Float3);bs.CreateInput('normal',Sdf.ValueTypeNames.Normal3f).ConnectToSource(tex.ConnectableAPI(),'rgb')
        elif kind=='roughness':tex.CreateOutput('r',Sdf.ValueTypeNames.Float);bs.GetInput('roughness').ConnectToSource(tex.ConnectableAPI(),'r')
        else:tex.CreateOutput('rgb',Sdf.ValueTypeNames.Float3);bs.GetInput('diffuseColor').ConnectToSource(tex.ConnectableAPI(),'rgb')
    m.CreateSurfaceOutput().ConnectToSource(bs.ConnectableAPI(),'surface');return m
def export(name,objects):
    path=OUT/(name+'.usdc');stage=Usd.Stage.CreateNew(str(path));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y);UsdGeom.SetStageMetersPerUnit(stage,1)
    is_terrain=name.startswith('terrain_');prefix='/Terrain' if is_terrain else '/Asset'
    root=UsdGeom.Xform.Define(stage,prefix);stage.SetDefaultPrim(root.GetPrim());cache={};triangles=0
    for index,d in enumerate(objects):
        mesh=UsdGeom.Mesh.Define(stage,prefix+('/Mesh' if is_terrain else f'/Mesh_{index:04d}'))
        if not is_terrain:mesh.GetPrim().SetDisplayName(d['name'])
        mesh.CreatePointsAttr([Gf.Vec3f(x,z,-y) for x,y,z in d['points']]);mesh.CreateFaceVertexCountsAttr([len(f) for f in d['faces']]);mesh.CreateFaceVertexIndicesAttr([i for f in d['faces'] for i in f]);mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        mesh.CreateNormalsAttr([Gf.Vec3f(x,z,-y) for x,y,z in d['normals']]);mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
        UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,UsdGeom.Tokens.faceVarying).Set([Gf.Vec2f(*v) for v in d['uv']])
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim());binding=UsdShade.MaterialBindingAPI(mesh)
        for i,mat in enumerate(d['materials']):
            key=json.dumps(mat,sort_keys=True)
            if key not in cache:cache[key]=material(stage,f'{prefix}/Materials/M{len(cache)}',mat)
            selected=[j for j,k in enumerate(d['material_indices']) if i==k]
            if not selected:continue
            subset=binding.CreateMaterialBindSubset('Faces'+str(i),selected);UsdShade.MaterialBindingAPI.Apply(subset.GetPrim());UsdShade.MaterialBindingAPI(subset).Bind(cache[key])
        binding.SetMaterialBindSubsetsFamilyType(UsdGeom.Tokens.partition);triangles+=sum(len(f)-2 for f in d['faces'])
    stage.GetRootLayer().Save();target=OUT/(name+'.usdz');assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(path)),str(target))
    assert Usd.Stage.Open(str(target)) and not UsdUtils.ComputeAllDependencies(str(target))[2]
    return {'filename':target.name,'meshes':len(objects),'triangles':triangles,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
reports=[]
for source in sorted(OUT.glob('*.json')):
    if source.name=='manifest.json':continue
    d=json.loads(source.read_text())
    if source.name.startswith('habitat_'):report=export(source.stem,d['objects']);report['grid']=[9,9];report['spawn_y_up']=[4,1.13,-.45]
    elif 'textures' in d:
        materials=[]
        for texture in d['textures']:
            stem=Path(texture).stem;materials.append({'textures':{'color':texture,'normal':stem+'_normal.png','roughness':stem+'_roughness.png'}})
        item={'name':d['name'],'points':d['vertices'],'faces':d['faces'],'normals':d['normals'],'uv':d['uv'],'material_indices':d['material_indices'],'materials':materials}
        report=export('terrain_'+d['name'],[item])
    else:continue
    reports.append(report);print(report['filename'],report['triangles'],'triangles')
(OUT/'manifest.json').write_text(json.dumps(reports,indent=2)+'\n')
