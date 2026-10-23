"""Soft local arm extension with a geodesically pinned shoulder boundary."""
import heapq
import numpy as np

def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

def shapes(pose,faces,indices,weights,joint_names,joint_points,unit,floor,extension,compression):
    neighbors=[set() for _ in pose]
    for a,b,c in faces:neighbors[a].update([b,c]);neighbors[b].update([a,c]);neighbors[c].update([a,b])
    normalized=pose/unit;normalized[:,2]-=floor/unit;offsets=[];report={}
    for side,sign in [('L',1),('R',-1)]:
        arm={i for i,n in enumerate(joint_names) if n.split('/')[-1] in [x+'_'+side for x in ['Shoulder','Bicep','Forearm','Hand']]+['Hand_'+side+'_end']}
        strength=np.sum(weights*np.isin(indices,list(arm)),axis=1)
        region=(strength>.55)&(normalized[:,0]*sign>.40)&(normalized[:,2]>.80)&(normalized[:,2]<1.68)
        distance=np.full(len(pose),np.inf);queue=[]
        for i in np.where(region)[0]:
            if any(not region[j] for j in neighbors[i]):distance[i]=0;heapq.heappush(queue,(0,int(i)))
        while queue:
            d,i=heapq.heappop(queue)
            if d>distance[i]:continue
            for j in neighbors[i]:
                nd=d+np.linalg.norm(pose[j]-pose[i])/unit
                if region[j] and nd<distance[j]:distance[j]=nd;heapq.heappush(queue,(nd,int(j)))
        falloff=np.zeros(len(pose));falloff[region]=smooth(distance[region]/.17)
        shoulder=joint_points['Bicep_'+side];tip=joint_points['Hand_'+side+'_end'];axis=tip-shoulder;axis/=np.linalg.norm(axis)
        vector=pose-shoulder;along=np.outer(vector@axis,axis);radial=vector-along
        for stretch in [1+extension,1-compression]:
            delta=(along*(stretch-1)+radial*(1/np.sqrt(stretch)-1))*falloff[:,None]
            delta[~region]=0;offsets.append(delta)
        report[side]={'regionVertexIds':np.where(region)[0].tolist(),'pinnedBoundaryVertices':int(np.sum(region&(falloff==0))),'maximumRequestedAxialStretch':1+extension,'maximumRequestedReturnCompression':1-compression,'radialCompensation':'inverse square root of axial scale; tip stays full; seam falloff reduces realized stretch'}
    return offsets,report
