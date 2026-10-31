#!/usr/bin/env python3
"""Package the locally rebuilt, source-pinned designElectronics WebAssembly."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
source=root.parents[2]/'.build/design-electronics-rebuilt'
expected={'designElectronics.js':'4d6c5602fbd164465144b9edf223cdb8b7b6bac57eca99905dd81d56359d2c22','designElectronics.wasm':'1fb748273aeed5f3b74d0993ec9381548b341704f4c75f05ff60928078d2a693','designElectronics.data':'b47f7a58ff1e8768885267b349018d60932c535938a301c0f3b6a2b0c5f8a7ed'}
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
