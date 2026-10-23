"""Offline USD playback/blending smoke check; does not modify the package or native app."""
from pathlib import Path
import json,math
import numpy as np
from pxr import Usd,UsdGeom,UsdSkel,Gf,Vt
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=REPO/'Assets/Handoff/FibuWalk'
s=Usd.Stage.Open(str(REPO/'Assets/Models/FibuWalk/Fibu.Walk.usdz'));meta=json.loads((OUT/'timeline.json').read_text());anim=next(UsdSkel.Animation(p) for p in s.Traverse() if p.IsA(UsdSkel.Animation));sk=next(UsdSkel.Skeleton(p) for p in s.Traverse() if p.IsA(UsdSkel.Skeleton));body=next(UsdGeom.Mesh(p) for p in s.Traverse() if p.IsA(UsdGeom.Mesh));binding=UsdSkel.BindingAPI(body);rest=np.array(body.GetPointsAttr().Get());offsets=[np.array(UsdSkel.BlendShape(s.GetPrimAtPath(p)).GetOffsetsAttr().Get()) for p in binding.GetBlendShapeTargetsRel().GetTargets()]
channels=[anim.GetTranslationsAttr(),anim.GetRotationsAttr(),anim.GetScalesAttr(),anim.GetBlendShapeWeightsAttr()];neutral=[attr.Get() for attr in channels]
review=UsdSkel.Animation.Define(s,'/WalkTransitionReview');review.CreateJointsAttr(anim.GetJointsAttr().Get());review.CreateBlendShapesAttr(anim.GetBlendShapesAttr().Get());UsdSkel.BindingAPI.Apply(sk.GetPrim()).CreateAnimationSourceRel().SetTargets([review.GetPath()]);dest=[review.CreateTranslationsAttr(),review.CreateRotationsAttr(),review.CreateScalesAttr(),review.CreateBlendShapeWeightsAttr()]
blend_seconds=meta['parameters']['transition_seconds']
def smooth(u):u=min(1,max(0,u));return u*u*(3-2*u)
def policy(t):
    # Analytic distance integral of eased speed; phase never assumes a fixed render frame rate.
    b=blend_seconds;stop=1.2
    if t<b:
        u=max(0,t/b);return smooth(u),b*(u**3-.5*u**4)
    if t<stop:return 1,b/2+t-b
    if t<stop+b:
        u=(t-stop)/b;return 1-smooth(u),b/2+stop-b+b*(u-u**3+.5*u**4)
    return 0,stop

def evaluate(t,speed_factor):
    alpha,integral=policy(t);phase=(integral*meta['recommendedSpeedAtHeight2_7']*speed_factor/meta['strideDistanceAtHeight2_7'])%1;sample=phase*(meta['samples']-1)
    sampled=[attr.Get(sample) for attr in channels];values=[]
    for index,(base,target) in enumerate(zip(neutral,sampled)):
        if index==1:values.append(Vt.QuatfArray([Gf.Slerp(alpha,a,b) for a,b in zip(base,target)]))
        elif index==0:values.append(Vt.Vec3fArray(((1-alpha)*np.array(base)+alpha*np.array(target)).tolist()))
        elif index==2:values.append(Vt.Vec3hArray(((1-alpha)*np.array(base)+alpha*np.array(target)).tolist()))
        else:values.append(Vt.FloatArray((alpha*np.array(target)).tolist()))
    for attr,value in zip(dest,values):attr.Set(value)
    c=UsdSkel.Cache()
    for p in s.Traverse():
        if p.IsA(UsdSkel.Root):c.Populate(UsdSkel.Root(p),Usd.PrimDefaultPredicate)
    q=c.GetSkelQuery(sk);sq=c.GetSkinningQuery(body.GetPrim());vertices=rest+sum((off*w for off,w in zip(offsets,values[3])),np.zeros_like(rest));v=Vt.Vec3fArray(vertices.tolist());assert sq.ComputeSkinnedPoints(q.ComputeSkinningTransforms(),v);return np.array(v)
unit=meta['skeletonUnitsPerCanonicalUnit'];first=evaluate(0,1);floor=first[:,2].min();summaries=[]
for rate in [.6,1,1.4]:
    frames=np.array([evaluate(float(t),rate) for t in np.linspace(0,1.6,97)])
    assert np.isfinite(frames).all() and np.max(np.abs(frames[-1]-first))/unit<1e-5
    ground=float((frames[:,:,2].min()-floor)/unit);jump=float(np.linalg.norm(np.diff(frames,axis=0),axis=2).max()/unit)
    assert ground>-.02 and jump<.12,(rate,ground,jump)
    summaries.append({'speedFactor':rate,'samples':len(frames),'minGroundOffset':ground,'maxVertexStepAt60fps':jump,'endsAtExactNeutral':True})
# The analytically integrated policy is sampled under distinct frame schedules.
phases=[]
for schedule in [[1/60],[1/30],[.011,.026,.019,.013]]:
    t=0;distance=0;i=0
    while t<1.6:
        end=min(1.6,t+schedule[i%len(schedule)]);distance+=(policy(end)[1]-policy(t)[1])*meta['recommendedSpeedAtHeight2_7'];t=end;i+=1
    phases.append(distance/meta['strideDistanceAtHeight2_7'])
assert max(phases)-min(phases)<1e-10
report={'scope':'Offline sampled USD local-transform and morph blends; native SceneKit starts/stops/turns still require local visual checks. No package was modified.','blendSeconds':blend_seconds,'startStopTrials':summaries,'distanceDrivenPhaseAcrossFrameSchedules':phases,'nativeTurnAndTerrainValidation':'pending local integration'}
(OUT/'blend-review.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: eased start/stop at 0.6x, 1x, 1.4x; exact neutral returns; frame-schedule independent distance phase')
