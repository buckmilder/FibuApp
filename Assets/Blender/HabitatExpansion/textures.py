"""Original seamless color textures for six additional habitat materials."""
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent/'textures';root.mkdir(exist_ok=True)
n=512;x,y=np.meshgrid(np.arange(n)/n,np.arange(n)/n);z=1-y
rng=np.random.default_rng(4917)
cloud=sum(np.sin(2*np.pi*(a*x+b*y)+p)*w for a,b,p,w in [(1,2,.4,.04),(3,1,2,.022),(4,5,1,.012),(13,9,3,.005)])
grain=rng.normal(0,.007,(n,n))
def color(c):return np.broadcast_to(np.array(c),(n,n,3)).copy()
def save(name,c):Image.fromarray(np.uint8(np.clip(c,0,1)*255)).save(root/(name+'.png'))
for theme in ['meadow','sand','limestone','cobble','timber','volcanic']:
 for face in ['side','top']:
    if theme=='meadow':
        c=color((.53,.72,.28) if face=='top' else (.64,.43,.25))
        if face=='side':
            c+=(.023*np.sin(2*np.pi*(z*3+.03*np.sin(x*6.28))))[...,None]
            edge=.79+.018*np.sin(x*6.28*7)+.011*np.sin(x*6.28*13)
            mask=z>edge;c[mask]=np.array((.38,.60,.19))
    elif theme=='sand':
        c=color((.89,.79,.56) if face=='top' else (.78,.65,.43))
        c+=(.012*np.sin(2*np.pi*(y*7+.06*np.sin(x*6.28))))[...,None]
        for _ in range(100):
            cx,cy=rng.random(2);dx=np.minimum(abs(x-cx),1-abs(x-cx));dy=np.minimum(abs(y-cy),1-abs(y-cy))
            mask=dx**2+dy**2<rng.uniform(.001,.004)**2;c[mask]-=.10
    elif theme=='limestone':
        c=color((.77,.76,.66) if face=='top' else (.64,.65,.57))
        for i in range(3):
            crack=abs(np.sin(2*np.pi*(y+i*.31+.018*np.sin(x*12.56))))<.012
            c[crack]-=.07
    elif theme=='cobble':
        # Periodic jittered Voronoi stones, with broad mortar and softly shaded rims.
        distances=[];colors=[]
        for a in range(4):
            for b in range(4):
                cx=(a+.5+rng.uniform(-.22,.22))/4;cy=(b+.5+rng.uniform(-.22,.22))/4
                dx=np.minimum(abs(x-cx),1-abs(x-cx));dy=np.minimum(abs(y-cy),1-abs(y-cy))
                distances.append(np.sqrt(dx*dx+dy*dy));colors.append(np.array((.52,.56,.49))+rng.uniform(-.055,.055))
        d=np.stack(distances);idx=d.argmin(axis=0);nearest=np.partition(d,1,axis=0)
        gap=nearest[1]-nearest[0];c=np.array(colors)[idx]
        mortar=np.clip(gap/.023,0,1);c=c*mortar[...,None]+np.array((.29,.33,.28))*(1-mortar[...,None])
        c+=(np.clip(gap/.045,0,1)*.025)[...,None]
    elif theme=='timber':
        u=x*4;seam=np.minimum(u%1,1-u%1)<.018
        c=color((.65,.42,.22) if face=='top' else (.51,.30,.15))
        c+=(.025*np.sin(2*np.pi*(x*31+.13*np.sin(y*6.28*2)))+.012*np.sin(x*6.28*68))[...,None]
        c[seam]-=.14
    else:
        c=color((.28,.28,.30) if face=='top' else (.23,.23,.25))
        for _ in range(100):
            cx,cy=rng.random(2);dx=np.minimum(abs(x-cx),1-abs(x-cx));dy=np.minimum(abs(y-cy),1-abs(y-cy))
            r=rng.uniform(.004,.017);mask=(dx/r)**2+(dy/r)**2<1;c[mask]-=.045
    c+=(cloud+grain)[...,None];save(theme+'_'+face,c)
print('Generated twelve original 512px textures')
