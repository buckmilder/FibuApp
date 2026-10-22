"""Generate original seamless hand-painted-style color textures; Python + NumPy + Pillow."""
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent/'textures'; root.mkdir(exist_ok=True)
n=512
x,y=np.meshgrid(np.arange(n)/n,np.arange(n)/n)
rng=np.random.default_rng(20261022)
def noise():
    a=np.zeros((n,n))
    for freq,amp in [(1,.4),(2,.22),(4,.13),(8,.07),(16,.035),(32,.018)]:
        for _ in range(4):
            a+=amp/4*np.sin(2*np.pi*(rng.integers(0,freq+1)*x+rng.integers(1,freq+1)*y)+rng.uniform(0,6.28))
    return a
def mix(a,b,t):return np.array(a)[None,None,:]*(1-t[...,None])+np.array(b)[None,None,:]*t[...,None]
def save(name,c):Image.fromarray(np.uint8(np.clip(c,0,1)*255)).save(root/(name+'.png'))
for name in ['golden','forest','lime']:
    cloud=noise(); fine=rng.normal(0,.007,(n,n)); z=1-y
    if name=='golden':
        side=mix((.69,.37,.12),(.91,.64,.29),np.clip(.48+cloud*1.5,0,1))
        bands=.025*np.sin(2*np.pi*(z*4+.06*np.sin(x*6.28)))
        side+=bands[...,None]
        rim=(z>.88+.012*np.sin(2*np.pi*x*3)).astype(float)
        side=mix((0,0,0),(0,0,0),rim)+side*(1-rim[...,None])+np.array([.94,.72,.36])*rim[...,None]
        top=mix((.88,.64,.28),(1,.84,.48),np.clip(.55+cloud,0,1))
    elif name=='forest':
        side=mix((.45,.26,.12),(.69,.45,.25),np.clip(.55+cloud,0,1))
        side+=(.035*np.sin(2*np.pi*(z*3+.025*np.sin(x*12.56))))[...,None]
        edge=.80+.025*np.sin(x*6.28*5)+.012*np.sin(x*6.28*11)
        turf=np.clip((z-edge)/.012,0,1)
        grass=mix((.035,.27,.16),(.09,.43,.25),np.clip(.50+cloud*1.5,0,1))
        side=side*(1-turf[...,None])+grass*turf[...,None]
        top=mix((.045,.32,.19),(.13,.49,.29),np.clip(.5+cloud*1.3,0,1))
    else:
        wave=.018*np.cos(x*6.28*7)+.008*np.cos(x*6.28*14)
        band=(np.sin((z+wave)*6*np.pi)>.15).astype(float)
        side=mix((.32,.52,.14),(.49,.67,.22),band*.72+.12)
        side+=(cloud*.14)[...,None]
        top=mix((.40,.64,.16),(.63,.79,.29),np.clip(.5+cloud,0,1))
    side+=fine[...,None];top+=fine[...,None]
    # Small muted mineral flecks / grass strokes, periodic across borders.
    for _ in range(140):
        cx,cy=rng.random(2); dx=np.minimum(abs(x-cx),1-abs(x-cx));dy=np.minimum(abs(y-cy),1-abs(y-cy))
        mask=(dx/(.002+rng.random()*.004))**2+(dy/(.002+rng.random()*.006))**2<1
        side[mask]+=.045;top[mask]+=.025
    save(name+'_side',side); save(name+'_top',top)
print('Generated six 512px color textures')
