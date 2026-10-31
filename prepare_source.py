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

EM_JS(void, de_js_project_save, (int as_new), {
    parent.postMessage({codiElectronics: as_new ? "save-as" : "save-project"}, location.origin);
});
EM_JS(void, de_js_project_replaced, (), {
    parent.postMessage({codiElectronics: "project-replaced"}, location.origin);
});

'''
p.write_text(s[:start]+bridge+s[end:])

def patch(path, expected_hash, replacements):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_hash:raise ValueError('Unexpected upstream source: '+str(path))
    text=data.decode()
    for before,after in replacements:
        if text.count(before)!=1:raise ValueError('Bridge patch did not match: '+str(path))
        text=text.replace(before,after)
    path.write_text(text)

web=p.read_text();marker='extern "C" EMSCRIPTEN_KEEPALIVE void de_web_opened(const char* path) {'
if web.count(marker)!=1:raise ValueError('Missing web entry point')
web=web.replace(marker,'''static int codi_document_epoch = 0;
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_epoch() { return codi_document_epoch; }
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_revision() {
    return g_webApp ? g_webApp->doc.revision : -1;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_snapshot(const char* path) {
    if (!g_webApp || !path) return 0;
    g_webApp->doc.syncWireEnds();
    return writeTextFile(path, g_webApp->doc.serialize(true)) ? 1 : 0;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_load(const char* path) {
    return g_webApp && path && g_webApp->loadFile(path) ? 1 : 0;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_mark_saved(int revision) {
    if (!g_webApp || g_webApp->doc.revision != revision) return 0;
    g_webApp->savedRevision = revision;
    return 1;
}

'''+marker)
marker='void webPickFile(const char* accept) {'
if web.count(marker)!=1:raise ValueError('Missing web picker')
web=web.replace(marker,'''void webProjectReplaced() {
#ifdef __EMSCRIPTEN__
    ++codi_document_epoch;
    de_js_project_replaced();
#endif
}

void webRequestProjectSave(bool as_new) {
#ifdef __EMSCRIPTEN__
    de_js_project_save(as_new ? 1 : 0);
#else
    (void)as_new;
#endif
}

'''+marker);p.write_text(web)
patch(root/'.build/design-electronics-upstream/src/app.h','833dbc8a289c6bf4fdf1088da23f51fce43aa9bd291554d23b193213e2ae695b',[
    ('void webPickFile(const char* accept);','void webPickFile(const char* accept);\nvoid webRequestProjectSave(bool as_new);\nvoid webProjectReplaced();')])
patch(root/'.build/design-electronics-upstream/src/app.cpp','8903d18de4fdf8cee4b620a7574b44742a382caf0abfb137c86786793040e08c',[
    ('void App::confirmDiscard(std::function<void()> then) {','''void App::confirmDiscard(std::function<void()> then) {
#ifdef __EMSCRIPTEN__
    if (!dirty()) { then(); return; }
    ui.dialog("Unsaved changes", {"Save your project to My files first, or discard these changes."},
              {{"Cancel", nullptr, false}, {"Discard", then, false}});
    return;
#endif'''),
    ('void App::save() {','void App::save() {\n#ifdef __EMSCRIPTEN__\n    webRequestProjectSave(false);\n    return;\n#endif'),
    ('void App::saveAs() {','void App::saveAs() {\n#ifdef __EMSCRIPTEN__\n    webRequestProjectSave(true);\n    return;\n#endif'),
    ('        newProjectContents(doc);\n        filePath.clear();','        newProjectContents(doc);\n        webProjectReplaced();\n        filePath.clear();'),
    ('        examples()[i].build(doc);\n        doc.syncWireEnds();','        examples()[i].build(doc);\n        webProjectReplaced();\n        doc.syncWireEnds();'),
    ('    if (!doc.fromJson(j, &err)) { ui.dialog("Could not open file", {err}, {}); return false; }','    if (!doc.fromJson(j, &err)) { ui.dialog("Could not open file", {err}, {}); return false; }\n    webProjectReplaced();'),
    ('                case SDLK_H: if (sh) openHistory(); break;','                case SDLK_H: break;'),
    ('                case SDLK_K: if (sh) openCommitSheet(); break;','                case SDLK_K: break;'),
    ('    loadGitHubSettings();','    // Desktop account storage replaces the upstream GitHub integration.')])
patch(root/'.build/design-electronics-upstream/src/panels.cpp','41c71178b0640b9c5559956c662f5fd19b497edeb8366d678f0873b7e8e28758',[
    ('        item("Version History…", [this]() { openHistory(); }, sc("⇧H")),\n        item("Commit to GitHub…", [this]() { openCommitSheet(); }, sc("⇧K")),\n        item(githubConnected() ? "GitHub Account (@" + gh.login + ")…" : "Connect GitHub…", [this]() { openGitHubAccount(); }),\n','')])
patch(root/'.build/design-electronics-upstream/CMakeLists.txt','c382dd58bdb89ac37d55bcd7585e8de7f8afa5299a92b2e6c8081677c925148e',[
    ('"-sEXPORTED_FUNCTIONS=[\'_main\',\'_de_web_opened\']"','"-sEXPORTED_FUNCTIONS=[\'_main\',\'_de_web_opened\',\'_de_web_epoch\',\'_de_web_revision\',\'_de_web_snapshot\',\'_de_web_load\',\'_de_web_mark_saved\']"')])
print('Applied desktop file bridge to pinned upstream source')
