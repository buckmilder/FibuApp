#!/usr/bin/env python3
"""Validate/copy artist PNG flipbooks losslessly, or decode a reference GIF.
Nothing is activated in the app. PNG input bytes are copied exactly.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,math
from PIL import Image

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate(root):
    root=Path(root).resolve();manifest=json.loads((root/'mouth.json').read_text())
    if manifest.get('format')!='fibu-mouth-art' or manifest.get('version')!=1:raise ValueError('Expected fibu-mouth-art version 1')
    canvas=manifest['canvas'];size=(canvas['width'],canvas['height'])
    if any(type(v)!=int or v<1 or v>4096 for v in size):raise ValueError('Canvas dimensions must be integers from 1 to 4096')
    anchor=manifest['registration']['anchor_px']
    if len(anchor)!=2 or any(type(v) not in (int,float) for v in anchor) or not 0<=anchor[0]<=size[0] or not 0<=anchor[1]<=size[1]:raise ValueError('Anchor must lie within the canvas')
    clips=manifest['clips'];ids=set();files={};records=[]
    if not clips:raise ValueError('At least one clip is required')
    for clip in clips:
        name=clip['id']
        if not isinstance(name,str) or not name or name in ids:raise ValueError('Clip IDs must be unique nonempty strings')
        ids.add(name)
        if type(clip.get('loop'))!=bool or clip.get('end_behavior') not in ['hold_last','return_to_smile']:raise ValueError('Specify loop and end_behavior')
        if not clip['frames']:raise ValueError('Each clip needs frames')
        total=0
        for frame in clip['frames']:
            rel=frame['file'];path=(root/rel).resolve()
            if Path(rel).is_absolute() or '..' in Path(rel).parts or not path.is_relative_to(root) or Path(rel).suffix.lower()!='.png':raise ValueError('Frame must be a PNG inside the art folder')
            duration=frame['duration_ms']
            if type(duration) not in (int,float) or not math.isfinite(duration) or duration<=0:raise ValueError('Frame durations must be positive finite milliseconds')
            with Image.open(path) as im:
                if im.format!='PNG' or im.mode!='RGBA' or im.size!=size:raise ValueError(f'{rel}: export a full-canvas {size} RGBA PNG')
            files[rel]=digest(path);total+=duration
        records.append({'id':name,'duration_ms':total,'frames':len(clip['frames'])})
    if 'source_gif' in manifest:
        ref=manifest['source_gif'];rel=ref['file'];path=(root/rel).resolve()
        if Path(rel).is_absolute() or '..' in Path(rel).parts or not path.is_relative_to(root) or path.suffix.lower()!='.gif' or digest(path)!=ref['sha256']:raise ValueError('Invalid original GIF reference')
    return manifest,files,records

def import_png(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    manifest,files,records=validate(source)
    if destination.exists():raise ValueError('Output already exists; choose a new version folder')
    if destination==source or source in destination.parents:raise ValueError('Output must be outside source folder')
    destination.mkdir(parents=True)
    for rel,sha in files.items():
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,target)
        assert digest(target)==sha
    if 'source_gif' in manifest:
        rel=manifest['source_gif']['file'];target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,target);assert digest(target)==manifest['source_gif']['sha256']
    shutil.copyfile(source/'mouth.json',destination/'mouth.json')
    report={'format':'fibu-mouth-art-import','version':1,'png_bytes_unchanged':True,'resized':False,'cropped':False,'redrawn':False,'frame_sha256':files,'clips':records,'source_manifest_sha256':digest(source/'mouth.json')}
    (destination/'import-report.json').write_text(json.dumps(report,indent=2)+'\n');return report

def decode_gif(source,destination,clip_id):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Output already exists; choose a new version folder')
    # Pillow applies GIF disposal/compositing on seek. Export the entire canvas,
    # never just the GIF optimized dirty rectangle.
    frames=[]
    with Image.open(source) as gif:
        if gif.format!='GIF':raise ValueError('Expected a GIF')
        size=gif.size;source_loop=gif.info.get('loop')
        for i in range(gif.n_frames):
            gif.seek(i);duration=gif.info.get('duration',0)
            if duration<=0:raise ValueError('GIF has a zero/missing duration; provide timed PNGs instead')
            frames.append((gif.convert('RGBA').copy(),duration))
    (destination/'frames').mkdir(parents=True)
    entries=[]
    for i,(image,duration) in enumerate(frames):
        rel=f'frames/{i:04d}.png';image.save(destination/rel)
        with Image.open(destination/rel) as result:assert result.tobytes()==image.tobytes()
        entries.append({'file':rel,'duration_ms':duration})
    (destination/'source').mkdir();shutil.copyfile(source,destination/'source/original.gif')
    manifest={'format':'fibu-mouth-art','version':1,'canvas':{'width':size[0],'height':size[1]},'registration':{'anchor_px':[size[0]/2,size[1]/2]},'source_gif':{'file':'source/original.gif','sha256':digest(source),'loop_count':source_loop},'clips':[{'id':clip_id,'loop':False,'end_behavior':'hold_last','frames':entries}]}
    (destination/'mouth.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(destination)
    return {'decoded_frames':len(frames),'duration_ms':sum(d for _,d in frames),'full_canvas_pixels_unchanged_after_decode':True,'note':'GIF palette/transparency limitations remain. No retiming or registration shift was applied.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path);p.add_argument('--gif',action='store_true');p.add_argument('--clip',default='eat');args=p.parse_args()
    try:
        if args.gif:
            if args.output is None:p.error('--gif needs --output')
            report=decode_gif(args.source,args.output,args.clip)
        elif args.output:report=import_png(args.source,args.output)
        else:
            _,files,clips=validate(args.source);report={'valid':True,'unique_pngs':len(files),'clips':clips}
        print(json.dumps(report,indent=2))
    except (ValueError,KeyError,OSError,TypeError) as e:p.exit(1,f'Art import rejected: {e}\n')
if __name__=='__main__':main()
