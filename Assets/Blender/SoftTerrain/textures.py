"""Original, periodic, broad-scale painted turf and three-band earth. No foliage meshes."""
from pathlib import Path
import math,json,hashlib
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];DEST=ROOT/'textures';DEST.mkdir(exist_ok=True)
N=1024;x,y=np.meshgrid(np.arange(N)/N,np.arange(N)/N);rng=np.random.default_rng(73609)
styles={'forest':((72,124,57),(144,101,66)),'lime':((143,181,53),(168,117,70)),'meadow':((113,159,57),(162,111,68))}
cloud=.5*np.sin(math.tau*(x+y))+.25*np.cos(math.tau*(2*x-y))+.15*np.sin(math.tau*(x-3*y))
# Shared leaf layout: large, quiet strokes rather than hundreds of tiny marks.
leaves=[]
for i in range(32):leaves.append((rng.uniform(0,N),rng.uniform(0,N),rng.uniform(110,175),rng.uniform(42,74),rng.uniform(0,math.tau),rng.uniform(-1,1)))
records=[]
for theme,(green,earth) in styles.items():
    color=np.array(green,dtype=float)+cloud[...,None]*5;relief=np.zeros((N,N))
    for cx,cy,length,width,angle,tone in leaves:
        dx=((x*N-cx+N/2)%N)-N/2;dy=((y*N-cy+N/2)%N)-N/2
        u=(dx*math.cos(angle)+dy*math.sin(angle))/length
        v=(-dx*math.sin(angle)+dy*math.cos(angle))/width
        radius=u*u+(v/(.9-.16*np.clip(u,-1,1)))**2
        amount=np.clip((1-radius)*7,0,1);amount=amount*amount*(3-2*amount)
        dome=np.maximum(0,1-radius)**.8
        leafcolor=np.array(green)+tone*6+(dome[...,None]*13-4)
        color=color*(1-amount[...,None])+leafcolor*amount[...,None]
        relief=relief*(1-amount)+dome*amount
    top=Image.fromarray(np.uint8(np.clip(color,0,255)));top.save(DEST/f'{theme}_top.png')
    b1=.32+.024*np.sin(math.tau*x)+.012*np.cos(math.tau*3*x)
    b2=.68+.026*np.sin(math.tau*(x+.21))+.009*np.cos(math.tau*2*x)
    band=np.where(y<b1,0,np.where(y<b2,1,2))
    shifts=np.array([[-10,-8,-5],[3,2,0],[14,10,5]])
    soil=np.array(earth)+shifts[band]+cloud[...,None]*2
    # Broad, gently feathered layer boundaries; retain exactly three readable earth bands.
    side=Image.fromarray(np.uint8(np.clip(soil,0,255))).filter(ImageFilter.GaussianBlur(1.2));side.save(DEST/f'{theme}_side.png')
    for face,color in [('top',top),('side',side)]:
        # Keep soil normal neutral; top relief is broad and low-amplitude.
        if face=='top':
            dy=(np.roll(relief,-1,axis=0)-np.roll(relief,1,axis=0))*5
            dx=(np.roll(relief,-1,axis=1)-np.roll(relief,1,axis=1))*5
            normals=np.stack([-dx,-dy,np.ones_like(dx)],axis=2);normals/=np.linalg.norm(normals,axis=2)[...,None]
            Image.fromarray(np.uint8(np.clip(normals*.5+.5,0,1)*255)).save(DEST/f'{theme}_{face}_normal.png')
        else:Image.new('RGB',(N,N),(128,128,255)).save(DEST/f'{theme}_{face}_normal.png')
        Image.new('L',(N,N),235).save(DEST/f'{theme}_{face}_roughness.png')
        for suffix in ['', '_normal','_roughness']:
            p=DEST/f'{theme}_{face}{suffix}.png';target=REPO/'Tools/HabitatEditor/assets/textures'/p.name;target.write_bytes(p.read_bytes());records.append({'file':str(target.relative_to(REPO)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'texture-manifest.json').write_text(json.dumps({'resolution':[N,N],'leafStrokesPerTile':32,'soilBands':3,'maps':records},indent=2)+'\n');print('Updated forest, lime and meadow maps')
