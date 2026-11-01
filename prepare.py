#!/usr/bin/env python3
"""Package the locally rebuilt, source-pinned designElectronics WebAssembly."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
source=root.parents[2]/'.build/design-electronics-rebuilt'
expected={'designElectronics.js':'8970e5070019ff4d9d82897d9d82554582815e7729b19dae4c0cb7dfd19ce7d5','designElectronics.wasm':'ad97043a7e58f0d17bf8607187b38c131e4e760714cb1616448854e9939cf631','designElectronics.data':'b47f7a58ff1e8768885267b349018d60932c535938a301c0f3b6a2b0c5f8a7ed'}
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
