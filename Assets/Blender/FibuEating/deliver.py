"""Copy review outputs; assemble animated GIF and annotated expression contact sheet."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=ROOT/'generated';MODELS=REPO/'Assets/Models/FibuEating';HANDOFF=REPO/'Assets/Handoff/FibuEating';MODELS.mkdir(exist_ok=True);HANDOFF.mkdir(exist_ok=True)
assert len(list((OUT/'frames').glob('*.png')))==43,'Render the complete animation before delivery'
stamp=json.loads((OUT/'render-source.json').read_text());assert stamp['packageSHA256']==hashlib.sha256((OUT/'Fibu.Eat.usdz').read_bytes()).hexdigest();assert stamp['dataSHA256']==hashlib.sha256((OUT/'preview-data.json').read_bytes()).hexdigest()
shutil.copy2(OUT/'Fibu.Eat.usdz',MODELS/'Fibu.Eat.usdz');shutil.copytree(OUT/'source/EatingTextures',MODELS/'EatingTextures',dirs_exist_ok=True)
anchors=json.loads((OUT/'face-anchors.json').read_text());data=json.loads((OUT/'preview-data.json').read_text())
for anchor in anchors['anchors']:anchor['vertexIndices']=data['faces'][anchor['triangle']]
(HANDOFF/'face-anchors.json').write_text(json.dumps(anchors,indent=2)+'\n')
for name in ['timeline.json','skins.json','validation.json','arm-region.json','render-source.json']:shutil.copy2(OUT/name,HANDOFF/name)
frames=[Image.open(p).convert('RGB') for p in sorted((OUT/'frames').glob('*.png'))]
palette=Image.new('RGB',(frames[0].width*7,frames[0].height))
for i,f in enumerate(frames[::7][:7]):palette.paste(f,(i*f.width,0))
palette=palette.quantize(colors=192)
converted=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames];durations=[70 if i%3==0 else 60 if i%3==1 else 70 for i in range(42)]+[600]
converted[0].save(HANDOFF/'eating-preview.gif',save_all=True,append_images=converted[1:],duration=durations,loop=0,disposal=2)
# Contact sheet uses the final animation renders, not stale intermediate stills.
labels=[('Smile',0),('Open / reach',.6),('Bite',.93),('Lick',1.2),('Cheek puff',1.8),('Swallow',2.1),('Happy',2.4)]
sheet=Image.new('RGB',(4*300,2*350),(30,43,42));draw=ImageDraw.Draw(sheet)
for i,(label,time) in enumerate(labels):
    index=min(42,round(time*15));f=ImageOps.contain(frames[index],(300,320));x=i%4*300;y=i//4*350;sheet.paste(f,(x+(300-f.width)//2,y+25));draw.text((x+12,y+7),f'{label} | {time:.2f}s',fill='white')
sheet.save(HANDOFF/'expressions.png')
print('Delivered model, textures, versioned runtime tracks, validation, GIF and expression sheet.')

folder=OUT/'skin-reviews'
records=json.loads((OUT/'skins.json').read_text())['skins']
if all((folder/(r['id']+'.png')).exists() for r in records):
    sheet=Image.new('RGB',(4*320,3*365),(30,43,42));draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(records):
        x=i%4*320;y=i//4*365;sheet.paste(Image.open(folder/(row['id']+'.png')),(x,y+25));draw.text((x+10,y+7),row['id'],fill='white')
    sheet.save(HANDOFF/'skins.png')
