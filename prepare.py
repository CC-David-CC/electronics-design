#!/usr/bin/env python3
"""Package the locally rebuilt, source-pinned designElectronics WebAssembly."""
import argparse,hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build-dir',type=Path,default=root.parents[2]/'.build/design-electronics-rebuilt')
source=parser.parse_args().build_dir
expected={'designElectronics.js':'87d41faf80c7008fb3f4d30a03eca2aec38dc051dd6795419c09304a19dbe3ac','designElectronics.wasm':'729552c90321f1dd7e2882e86f59b1ec05b3964153d99bb1462a74c4dd1a3526','designElectronics.data':'b47f7a58ff1e8768885267b349018d60932c535938a301c0f3b6a2b0c5f8a7ed'}
validated={}
for name,h in expected.items():
 data=(source/name).read_bytes()
 if hashlib.sha256(data).hexdigest()!=h:raise ValueError('Local build output differs; review before repinning: '+name)
 validated[name]=data
vendor=root/'vendor';vendor.mkdir(exist_ok=True)
for name,data in validated.items():
 (vendor/name).write_bytes(data)
for name in ('loader.js','index.html','frame.css'):shutil.copyfile(root/'frame'/name,vendor/name)
(root/'app.json').write_text(json.dumps({'assets':['vendor/'+x for x in [*expected,'loader.js','index.html','frame.css']]+['licenses/'+x.name for x in sorted((root/'licenses').glob('*.txt'))]},indent=2)+'\n')
print('Prepared source-pinned local WebAssembly build')
