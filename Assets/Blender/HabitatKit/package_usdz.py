"""Run with Python and the usd-core package installed."""
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils
import pathlib, json
root=pathlib.Path(__file__).resolve().parent
for source in sorted((root/'models').glob('*.json')):
    data=json.loads(source.read_text()); path=source.with_suffix('.usdc')
    stage=Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(stage,1)
    model=UsdGeom.Xform.Define(stage,'/Asset'); stage.SetDefaultPrim(model.GetPrim())
    mesh=UsdGeom.Mesh.Define(stage,'/Asset/Geometry')
    # Blender Z-up -> RealityKit Y-up. The model origin stays at the base center.
    mesh.CreatePointsAttr([Gf.Vec3f(x,z,-y) for x,y,z in data['vertices']])
    mesh.CreateFaceVertexCountsAttr([len(f) for f in data['faces']])
    mesh.CreateFaceVertexIndicesAttr([v for f in data['faces'] for v in f])
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
    binding=UsdShade.MaterialBindingAPI(mesh)
    for i,m in enumerate(data['materials']):
        mat=UsdShade.Material.Define(stage,f'/Asset/Materials/Material_{i}')
        shader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Surface'))
        shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*m['color']))
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.83)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        subset=binding.CreateMaterialBindSubset('Surface_'+str(i),[j for j,k in enumerate(data['material_indices']) if k==i])
        UsdShade.MaterialBindingAPI.Apply(subset.GetPrim()); UsdShade.MaterialBindingAPI(subset).Bind(mat)
    binding.SetMaterialBindSubsetsFamilyType(UsdGeom.Tokens.partition)
    stage.GetRootLayer().Save()
    target=source.with_suffix('.usdz')
    assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(path)),str(target))
    check=Usd.Stage.Open(str(target)); assert check and check.GetDefaultPrim()
    deps=UsdUtils.ComputeAllDependencies(str(target))
    assert not deps[2], deps[2]
    points=UsdGeom.Mesh(check.GetPrimAtPath('/Asset/Geometry')).GetPointsAttr().Get()
    assert points and min(p[1] for p in points)>-0.00001
    print(target.name,len(points),'vertices: package reopened, no unresolved dependencies')
