"""Paint a new nine-material set with original periodic organic surface details."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,math
ROOT=Path(__file__).resolve().parent;dest=ROOT/'textures';dest.mkdir(exist_ok=True)
themes=['golden','forest','lime','meadow','sand','limestone','cobble','timber','volcanic']
N=1024;rng=np.random.default_rng(9137)
x,y=np.meshgrid(np.arange(N)/N,np.arange(N)/N)
cloud=sum(np.sin(math.tau*(a*x+b*y)+rng.uniform(0,math.tau))*w for a,b,w in [(1,1,.022),(2,3,.018),(5,2,.012),(9,7,.004)])
for theme in themes:
    previous=ROOT.parent/('TerrainV2' if theme in themes[:3] else 'HabitatExpansion')/'textures'
    for face in ['top','side']:
        old=Image.open(previous/(theme+'_'+face+'.png')).convert('RGB').resize((N,N),Image.Resampling.LANCZOS)
        if theme in ['forest','lime','meadow'] and face=='top':
            base={'forest':(.17,.42,.24),'lime':(.53,.70,.27),'meadow':(.42,.62,.25)}[theme]
            color=np.clip(np.array(base)[None,None,:]+cloud[...,None],0,1)
            old=Image.fromarray(np.uint8(color*255))
        layer=Image.new('RGBA',(N,N));draw=ImageDraw.Draw(layer)
        if theme in ['forest','lime','meadow'] and face=='top':
            # Muted overlapping leaf strokes and a few small flower/seed flecks.
            for i in range(330):
                cx,cy=rng.integers(0,N,2);angle=rng.uniform(0,math.tau);length=rng.uniform(9,29);width=rng.uniform(3,9)
                shade=(185,203,91,48) if i%3 else (47,102,43,43)
                pts=[]
                for k in range(16):
                    t=k*math.tau/16;u=length*math.cos(t);v=width*math.sin(t)
                    pts.append((cx+u*math.cos(angle)-v*math.sin(angle),cy+u*math.sin(angle)+v*math.cos(angle)))
                for dx in [-N,0,N]:
                    for dy in [-N,0,N]:draw.polygon([(a+dx,b+dy) for a,b in pts],fill=shade)
            for i in range(16):
                cx,cy=rng.integers(8,N-8,2);c=(231,207,107,150) if i%3 else (230,225,184,125)
                for k in range(4):
                    a=k*math.tau/4;u=cx+3*math.cos(a);v=cy+3*math.sin(a);draw.ellipse((u-2,v-2,u+2,v+2),fill=c)
        else:
            # Mineral / grain marks: varied, quiet details rather than large photographic noise.
            for i in range(900 if theme in ['sand','golden','volcanic'] else 350):
                cx,cy=rng.integers(0,N,2);w=int(rng.integers(1,5));h=int(rng.integers(1,4));shade=(32,32,29,40) if i%2 else (245,231,189,38)
                draw.ellipse((cx-w,cy-h,cx+w,cy+h),fill=shade)
            if theme=='timber':
                for cx,cy in [(160,280),(690,780)]:
                    for r in [9,16,26,40]:draw.ellipse((cx-r*.45,cy-r,cx+r*.45,cy+r),outline=(73,39,17,80),width=2)
            if theme=='limestone':
                for _ in range(7):
                    cx,cy=rng.integers(50,N-100,2);pts=[(cx,cy),(cx+15,cy+20),(cx+12,cy+36),(cx+26,cy+55)]
                    draw.line(pts,fill=(72,78,66,55),width=2)
        result=Image.alpha_composite(old.convert('RGBA'),layer.filter(ImageFilter.GaussianBlur(.65))).convert('RGB')
        result.save(dest/(theme+'_'+face+'.png'))
        # Small, restrained surface normals and roughness maps; base color remains readable alone.
        a=np.array(result.resize((256,256)),dtype=float)/255;h=a.mean(axis=2)
        dx=(np.roll(h,-1,1)-np.roll(h,1,1))*.65;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*.65
        normal=np.stack((-dx,dy,np.ones_like(h)),axis=2);normal/=np.linalg.norm(normal,axis=2)[...,None]
        Image.fromarray(np.uint8((normal*.5+.5)*255)).save(dest/(theme+'_'+face+'_normal.png'))
        rough=np.clip(.83+(h-h.mean())*.2,.65,.95)
        Image.fromarray(np.uint8(rough*255)).save(dest/(theme+'_'+face+'_roughness.png'))
print('Nine materials: 18 painted color maps plus 36 normal/roughness maps')
