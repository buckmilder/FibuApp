"""Python + usd-core. Package textured, Y-up terrain for Apple's USD readers."""
from pathlib import Path
import json,shutil
from pxr import Usd,UsdGeom,UsdShade,Sdf,Gf,UsdUtils
ROOT=Path(__file__).resolve().parent
out=ROOT/'generated'
for source in sorted(out.glob('*.json')):
    data=json.loads(source.read_text());name='terrain_'+data['name']
    stage=Usd.Stage.CreateNew(str(out/(name+'.usdc')))
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y);UsdGeom.SetStageMetersPerUnit(stage,1)
    root=UsdGeom.Xform.Define(stage,'/Terrain');stage.SetDefaultPrim(root.GetPrim())
    mesh=UsdGeom.Mesh.Define(stage,'/Terrain/Mesh')
    mesh.CreatePointsAttr([Gf.Vec3f(x,z,-y) for x,y,z in data['vertices']])
    mesh.CreateFaceVertexCountsAttr([3]*len(data['faces']));mesh.CreateFaceVertexIndicesAttr([v for f in data['faces'] for v in f])
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateNormalsAttr([Gf.Vec3f(x,z,-y) for x,y,z in data['normals']]);mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    st=UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,UsdGeom.Tokens.faceVarying)
    st.Set([Gf.Vec2f(*uv) for uv in data['uv']])
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim());binding=UsdShade.MaterialBindingAPI(mesh)
    for i,texture in enumerate(data['textures']):
        shutil.copy2(ROOT/'textures'/texture,out/texture)
        mat=UsdShade.Material.Define(stage,f'/Terrain/Materials/M{i}')
        shader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Surface'));shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.86)
        shader.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(0)
        reader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('UV'));reader.CreateIdAttr('UsdPrimvarReader_float2')
        reader.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st');reader.CreateOutput('result',Sdf.ValueTypeNames.Float2)
        tex=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Color'));tex.CreateIdAttr('UsdUVTexture')
        tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(texture))
        tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
        for axis in ['S','T']:tex.CreateInput('wrap'+axis,Sdf.ValueTypeNames.Token).Set('repeat')
        tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(),'result')
        tex.CreateOutput('rgb',Sdf.ValueTypeNames.Float3)
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),'rgb')
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        subset=binding.CreateMaterialBindSubset('Faces'+str(i),[j for j,k in enumerate(data['material_indices']) if k==i])
        UsdShade.MaterialBindingAPI.Apply(subset.GetPrim());UsdShade.MaterialBindingAPI(subset).Bind(mat)
    binding.SetMaterialBindSubsetsFamilyType(UsdGeom.Tokens.partition)
    stage.GetRootLayer().Save()
    target=out/(name+'.usdz')
    assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(out/(name+'.usdc'))),str(target))
    check=Usd.Stage.Open(str(target));assert check and not UsdUtils.ComputeAllDependencies(str(target))[2]
    print(name,len(data['faces']),'triangles, textures packaged')
