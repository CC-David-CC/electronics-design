#!/usr/bin/env python3
"""Apply the reviewed desktop file bridge to the pinned upstream source."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=root/'.build/design-electronics-upstream/src/web.cpp'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!='f00a305798f899f92c3d86c968be73166da2f7cb9b3cda7acfed2b668c8397e5':raise ValueError('Unexpected upstream source or bridge already applied')
s=raw.decode();start=s.index('EM_JS(void, de_js_download');end=s.index('// Text fields:',start)
bridge='''EM_JS(void, de_js_download, (const char* path, const char* name), {
    const data = FS.readFile(UTF8ToString(path));
    parent.postMessage({codiElectronics: "save", name: UTF8ToString(name), data: data.slice()}, location.origin);
});

EM_JS(void, de_js_pick_file, (const char* accept), {
    parent.postMessage({codiElectronics: "open", accept: UTF8ToString(accept)}, location.origin);
});

'''
p.write_text(s[:start]+bridge+s[end:])
print('Applied desktop file bridge to pinned upstream source')
