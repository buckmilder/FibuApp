"""Pin an elastic hand-reach surface to a static torso; preserve original topology."""
import heapq
import numpy as np

def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)

def make_shapes(pose,faces,indices,weights,joint_names,joint_points,unit,floor,helper_poses):
    p=pose/unit;p[:,2]-=floor/unit
    right={i for i,n in enumerate(joint_names) if n.split('/')[-1] in ['Shoulder_R','Bicep_R','Forearm_R','Hand_R','Hand_R_end']}
    strength=np.sum(weights*np.isin(indices,list(right)),axis=1)
    region=(strength>.55)&(p[:,0]<-.40)&(p[:,2]>.80)&(p[:,2]<1.68)
    neighbors=[set() for _ in p]
    for a,b,c in faces:
        neighbors[a].update([b,c]);neighbors[b].update([a,c]);neighbors[c].update([a,b])
    distance=np.full(len(p),np.inf);queue=[]
    for i in np.where(region)[0]:
        if any(not region[j] for j in neighbors[i]):distance[i]=0;heapq.heappush(queue,(0,int(i)))
    while queue:
        d,i=heapq.heappop(queue)
        if d>distance[i]:continue
        for j in neighbors[i]:
            nd=d+np.linalg.norm(p[j]-p[i])
            if region[j] and nd<distance[j]:distance[j]=nd;heapq.heappush(queue,(nd,j))
    falloff=np.zeros(len(p));falloff[region]=smooth(distance[region]/.17)
    targets=[]
    for helper in helper_poses:
        delta=(helper-pose)/unit*falloff[:,None];delta[~region]=0;target=p+delta
        for _ in range(24):
            average=np.array([target[list(adj)].mean(axis=0) if adj else target[i] for i,adj in enumerate(neighbors)])
            target+=(average-target)*(.45*falloff[:,None])
        delta=target-p;delta[~region]=0;targets.append(delta*unit)
    info={'vertexIds':np.where(region)[0].tolist(),'movingVertexIds':np.where(falloff>0)[0].tolist(),
          'pinnedBoundaryVertices':int(np.sum(region&(falloff==0))),'helperShoulderAndUpperArmFixed':True,'helperForearmRadialScale':1.40,
          'method':'expanded helper-rig keyposes baked into isolated surface morphs; helper rotations/scales are not runtime skeletal tracks'}
    print('Elastic arm:',len(info['vertexIds']),'region vertices;',info['pinnedBoundaryVertices'],'fixed seam vertices',flush=True)
    return targets,info

def grip_path(pose,bite_pose,faces,region_ids,unit,floor):
    """A rolling contact on the palm; avoids floating food or a buried grip."""
    p=pose/unit;p[:,2]-=floor/unit;ids=np.array(region_ids);tri=np.array(faces)
    start=int(ids[np.linalg.norm(p[ids]-[-.78,-.52,1.14],axis=1).argmin()])
    # At the bite, the inner palm faces the mouth; pick its contact point.
    v=bite_pose/unit;v[:,2]-=floor/unit;t=v[tri];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=np.zeros_like(v)
    for j in range(3):np.add.at(norm,tri[:,j],cross)
    norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-10)
    candidates=ids[(p[ids,2]<1.3)&(p[ids,1]<-.22)&(p[ids,0]>-.9)]
    end=int(candidates[np.linalg.norm((v+norm*.11)[candidates]-[-.03,-.90,1.70],axis=1).argmin()])
    neighbors=[set() for _ in p]
    for a,b,c in tri:neighbors[a].update([b,c]);neighbors[b].update([a,c]);neighbors[c].update([a,b])
    allowed=set(region_ids);distance={start:0};previous={};queue=[(0,start)]
    while queue:
        d,i=heapq.heappop(queue)
        if d>distance[i]:continue
        if i==end:break
        for j in neighbors[i]:
            if j not in allowed:continue
            cost=np.linalg.norm(p[j]-p[i])*(1+5*max(0,1.1-(p[j,2]+p[i,2])/2));nd=d+cost
            if nd<distance.get(j,float('inf')):distance[j]=nd;previous[j]=i;heapq.heappush(queue,(nd,int(j)))
    path=[end]
    while path[-1]!=start:path.append(previous[path[-1]])
    path=path[::-1];length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p[path],axis=0),axis=1))];length/=length[-1]
    return path,length
