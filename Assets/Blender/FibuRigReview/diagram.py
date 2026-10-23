"""Draw measured skeleton lines over rendered neutral views; no invented anatomy."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,shutil
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];OUT=ROOT/'generated';DEST=REPO/'Assets/Handoff/FibuRigReview';data=json.loads((OUT/'rig.json').read_text());projection=json.loads((OUT/'projection.json').read_text());joints=data['joints'];by_name={j['name']:i for i,j in enumerate(joints)}
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,17);small=ImageFont.truetype(fontpath,14);title=ImageFont.truetype(fontpath,26)
visible=set(['Booty','Waist','Stomach','Chest','Neck','Face','Head','Head_end','Crotch_Bone']+[part+'_'+side for side in ['L','R'] for part in ['Shoulder','Bicep','Forearm','Hand','Thigh','Calf','Foot','Toe']]+['Hand_L_end','Hand_R_end','Toe_L_end','Toe_R_end'])
for view in ['front','side']:
 canvas=Image.new('RGB',(940,950),(23,31,37));canvas.paste(Image.open(OUT/(view+'.png')).convert('RGB'),(150,80));draw=ImageDraw.Draw(canvas);points=[(x+150,y+80) for x,y in projection[view]]
 draw.text((28,20),'Fibu - neutral skeleton / '+view.upper(),font=title,fill='white');draw.text((28,57),'Approved proportions model | actual source joint centers | x-ray overlay',font=small,fill=(183,198,207))
 for i,j in enumerate(joints):
  parent=j['parent']
  if j['name'] not in visible or parent<0 or joints[parent]['name'] not in visible:continue
  a,b=points[parent],points[i]
  if math.dist(a,b)<1:continue
  color=(107,216,255) if ('_L' in j['name'] or '_R' in j['name']) else (255,204,97)
  draw.line([a,b],fill=(16,25,30),width=9);draw.line([a,b],fill=color,width=4)
 for i,j in enumerate(joints):
  if j['name'] not in visible:continue
  x,y=points[i];draw.ellipse((x-5,y-5,x+5,y+5),fill=(255,246,215),outline=(18,27,32),width=2)
 if view=='front':
  labels=[('Head_end','Head tip',670,145),('Head','Head',670,225),('Face','Face',670,330),('Neck','Neck',670,390),('Chest','Chest',670,445),('Stomach','Belly',670,505),('Waist','Hips / waist',670,565),('Thigh_L','Hip joint',670,650),('Calf_L','Knee',670,710),('Foot_L','Ankle',670,770),('Shoulder_R','Shoulder',30,390),('Bicep_R','Upper arm',30,445),('Forearm_R','Elbow',30,510),('Hand_R','Hand',30,570)]
 else:
  labels=[('Head','Head',680,225),('Neck','Neck',680,390),('Chest','Chest',680,445),('Stomach','Belly',680,500),('Waist','Hips / waist',680,555),('Thigh_L','Hip joint',680,645),('Calf_L','Knee',680,710),('Foot_L','Ankle',680,775),('Toe_L_end','Toe',35,820),('Shoulder_L','Shoulder',30,350),('Bicep_L','Upper arm',30,415),('Forearm_L','Elbow',30,485),('Hand_L','Hand',30,550)]
 for name,label,x,y in labels:
  target=points[by_name[name]];width=draw.textlength(label,font=font);start=(x-8,y+10) if x>600 else (x+width+8,y+10)
  draw.line([start,target],fill=(176,191,201),width=1);draw.rectangle((x-3,y-2,x+width+3,y+23),fill=(23,31,37));draw.text((x,y),label,font=font,fill='white')
 draw.text((28,895),'Gold: spine / torso     Blue: arms / legs     Dots: joints',font=font,fill=(211,224,233));draw.text((28,925),'32 source joints; coincident root helpers omitted. Side view overlaps left/right limbs.',font=small,fill=(169,189,200))
 canvas.save(DEST/('skeleton-'+view+'.png'))
(DEST/'joint-centers.json').write_text(json.dumps({k:v for k,v in data.items() if k not in ['points','faces']},indent=2)+'\n');print('Saved front and side skeleton diagrams')
