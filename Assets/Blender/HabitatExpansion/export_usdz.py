"""Export new terrain with the shared pipeline, then export solid-mesh foliage."""
from pathlib import Path
import json
from pxr import Usd,UsdGeom,UsdShade,Sdf,Gf,UsdUtils
ROOT=Path(__file__).resolve().parent
script=(ROOT.parent/'TerrainV2/export_usdz.py').read_text()
script=script.replace("sorted(out.glob('*.json'))", "[p for p in sorted(out.glob('*.json')) if 'textures' in json.loads(p.read_text())]")
exec(compile(script,str(ROOT.parent/'TerrainV2/export_usdz.py'),'exec'))
for source in sorted((ROOT/'generated').glob('foliage_*.json')):
    data=json.loads(source.read_text());name=data['name'];out=ROOT/'generated'
    stage=Usd.Stage.CreateNew(str(out/(name+'.usdc')))
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y);UsdGeom.SetStageMetersPerUnit(stage,1)
    root=UsdGeom.Xform.Define(stage,'/Foliage');stage.SetDefaultPrim(root.GetPrim())
    mesh=UsdGeom.Mesh.Define(stage,'/Foliage/Mesh')
    mesh.CreatePointsAttr([Gf.Vec3f(x,z,-y) for x,y,z in data['vertices']])
    mesh.CreateFaceVertexCountsAttr([3]*len(data['faces']));mesh.CreateFaceVertexIndicesAttr([v for f in data['faces'] for v in f])
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateNormalsAttr([Gf.Vec3f(x,z,-y) for x,y,z in data['normals']]);mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim());binding=UsdShade.MaterialBindingAPI(mesh)
    for i,color in enumerate(data['colors']):
        material=UsdShade.Material.Define(stage,f'/Foliage/Materials/M{i}')
        shader=UsdShade.Shader.Define(stage,material.GetPath().AppendChild('Surface'));shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.85)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        subset=binding.CreateMaterialBindSubset('Faces'+str(i),[j for j,k in enumerate(data['material_indices']) if k==i])
        UsdShade.MaterialBindingAPI.Apply(subset.GetPrim());UsdShade.MaterialBindingAPI(subset).Bind(material)
    binding.SetMaterialBindSubsetsFamilyType(UsdGeom.Tokens.partition)
    stage.GetRootLayer().Save();target=out/(name+'.usdz')
    assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(out/(name+'.usdc'))),str(target))
    assert Usd.Stage.Open(str(target)) and not UsdUtils.ComputeAllDependencies(str(target))[2]
    print(name,len(data['faces']),'triangles')
