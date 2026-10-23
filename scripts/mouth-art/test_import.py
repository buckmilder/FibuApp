import unittest,tempfile,json,importlib.util
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('mouth_import',Path(__file__).with_name('import_art.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ArtImportTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.source=self.root/'art';(self.source/'frames').mkdir(parents=True)
  im=Image.new('RGBA',(32,32));im.putpixel((7,8),(27,63,125,87));im.save(self.source/'frames/000.png')
  self.manifest={'format':'fibu-mouth-art','version':1,'canvas':{'width':32,'height':32},'registration':{'anchor_px':[16,16]},'clips':[{'id':'eat','loop':False,'end_behavior':'hold_last','frames':[{'file':'frames/000.png','duration_ms':1000/24}]}]};self.write()
 def write(self):(self.source/'mouth.json').write_text(json.dumps(self.manifest))
 def test_exact_png_bytes_alpha_and_timing(self):
  report=module.import_png(self.source,self.root/'runtime');self.assertTrue(report['png_bytes_unchanged']);self.assertEqual((self.source/'frames/000.png').read_bytes(),(self.root/'runtime/frames/000.png').read_bytes());self.assertEqual(report['clips'][0]['duration_ms'],1000/24)
 def test_cropped_frame_rejected_without_output(self):
  Image.new('RGBA',(8,8)).save(self.source/'frames/000.png')
  with self.assertRaises(ValueError):module.import_png(self.source,self.root/'runtime')
  self.assertFalse((self.root/'runtime').exists())
 def test_escape_rejected(self):
  self.manifest['clips'][0]['frames'][0]['file']='../outside.png';self.write()
  with self.assertRaises(ValueError):module.validate(self.source)
 def test_no_output_overwrite(self):
  (self.root/'runtime').mkdir()
  with self.assertRaises(ValueError):module.import_png(self.source,self.root/'runtime')
 def test_gif_full_canvas_disposal_and_timing(self):
  a=Image.new('RGBA',(16,16),(255,0,0,255));b=Image.new('RGBA',(16,16));b.putpixel((3,4),(0,255,0,255));gif=self.root/'ref.gif';a.save(gif,save_all=True,append_images=[b],duration=[80,120],disposal=[1,2],loop=0)
  report=module.decode_gif(gif,self.root/'decoded','eat');self.assertEqual(report['duration_ms'],200)
  module.import_png(self.root/'decoded',self.root/'decoded-runtime');self.assertEqual(gif.read_bytes(),(self.root/'decoded-runtime/source/original.gif').read_bytes())
  with Image.open(gif) as source:
   for i in range(source.n_frames):
    source.seek(i)
    with Image.open(self.root/f'decoded/frames/{i:04d}.png') as output:self.assertEqual(source.convert('RGBA').tobytes(),output.tobytes())
if __name__=='__main__':unittest.main()
