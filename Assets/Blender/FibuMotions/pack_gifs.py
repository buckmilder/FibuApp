from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent/'generated'
for name,duration in [('Jump',115),('Sit',230)]:
    images=[Image.open(p).convert('RGB') for p in sorted((OUT/(name+'-frames')).glob('*.png'))]
    assert len(images)==13
    times=[duration]*13;times[-1]=600 if name=='Sit' else duration
    images[0].save(OUT/(name+'-preview.gif'),save_all=True,append_images=images[1:],duration=times,loop=0)
print('Packed Jump and Sit preview GIFs; GIF repetition is for review only')
