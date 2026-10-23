"""Package source renders as GIFs and pose sheets."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=ROOT/'generated';DEST=REPO/'Assets/Handoff/FibuWalk';meta=json.loads((DEST/'timeline.json').read_text());last=meta['samples']-1
sample_frames=list(range(0,last,2));durations=[]
for i,f in enumerate(sample_frames):
    end=sample_frames[i+1] if i+1<len(sample_frames) else last
    durations.append(round(end/meta['fps']*100)*10-round(f/meta['fps']*100)*10)
for view in ['front','side','angle']:
    frames=[Image.open(p).convert('RGB') for p in sorted((OUT/view).glob('*.png'))]
    assert len(frames)==len(sample_frames)
    width,height=frames[0].size;cols=7;palette=Image.new('RGB',(width*cols,height*math.ceil(len(frames)/cols)))
    for i,f in enumerate(frames):palette.paste(f,((i%cols)*width,(i//cols)*height))
    pal=palette.quantize(colors=256);images=[f.quantize(palette=pal) for f in frames]
    images[0].save(DEST/f'walk-{view}.gif',save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2)
    sheet=Image.new('RGB',(width*4,height+30),(29,42,43));draw=ImageDraw.Draw(sheet)
    for col,index in enumerate([round(len(frames)*q) for q in [0,.25,.5,.75]]):
        sheet.paste(frames[index],(col*width,30));draw.text((col*width+12,10),f'{view} - cycle {sample_frames[index]/last:.2f}',fill='white')
    sheet.save(DEST/f'poses-{view}.png')
    neutral=Image.open(OUT/('idle-'+view+'.png')).convert('RGB');comparison=Image.new('RGB',(width*2,height+30),(29,42,43));draw=ImageDraw.Draw(comparison);comparison.paste(neutral,(0,30));comparison.paste(frames[round(len(frames)/4)],(width,30));draw.text((12,10),'Approved neutral',fill='white');draw.text((width+12,10),'Walk passing pose',fill='white');comparison.save(DEST/f'neutral-comparison-{view}.png')
(DEST/'render-source.json').write_text(json.dumps({'packageSHA256':meta['packageSHA256'],'previewDataSHA256':hashlib.sha256((OUT/'preview-data.json').read_bytes()).hexdigest(),'views':['front','side','angle'],'framesPerView':len(sample_frames),'gifDurationMs':sum(durations)},indent=2)+'\n')
print('Packaged front, side and angle GIFs, pose sheets and neutral comparisons')
