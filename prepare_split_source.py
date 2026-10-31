#!/usr/bin/env python3
"""Apply the reviewed three-view patch after the desktop file bridge."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3]/'.build/design-electronics-upstream'
def patch(name,digest,changes):
 p=root/name;raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Unexpected bridged source: '+str(p))
 text=raw.decode()
 for before,after in changes:
  if text.count(before)!=1:raise ValueError('Split-view patch did not match: '+str(p))
  text=text.replace(before,after)
 p.write_text(text)
patch('src/app.h','65438bb1366b7eff4f7698f73c04a7b3e92554ad3df2188678fe8e5906134389',[
 ('    Rect rTop, rCanvas, rRight, rBottom, rBin, rInspector;', '''    Rect rTop, rCanvas, rRight, rBottom, rBin, rInspector;
    // Three viewports share this App's one Document and simulation.
    bool splitRequested = false, splitActive = false;
    Rect wholeCanvas, splitPane[NUM_VIEWS];''')])
patch('src/app.cpp','cf09f15392ed3c6dae691fcec36cdc0e623a607ed07491999703d36a49908a97',[
 ('''    } else rCode = Rect();
}''','''    } else rCode = Rect();
    wholeCanvas = rCanvas;
    bool nextSplit = splitRequested && !compact && wholeCanvas.w >= 1500 * s && wholeCanvas.h >= 300 * s;
    if (nextSplit != splitActive) for (auto& camera : cam) camera.valid = false;
    splitActive = nextSplit;
    if (splitActive) {
        float paneWidth = wholeCanvas.w / NUM_VIEWS;
        for (int v = 0; v < NUM_VIEWS; v++)
            splitPane[v] = Rect(wholeCanvas.x + v * paneWidth, wholeCanvas.y, paneWidth, wholeCanvas.h);
        rCanvas = splitPane[view];
    }
}'''),
 ('''    view = v;
    ui.clearFocus();''','''    view = v;
    if (splitActive) rCanvas = splitPane[view];
    ui.clearFocus();'''),
 ('''            Rect before = rCanvas;
            layout();
            for (auto& c : cam) if (c.valid) c.pan += rCanvas.center() - before.center();''','''            Rect before = rCanvas, beforePanes[NUM_VIEWS];
            bool wasSplit = splitActive;
            for (int v = 0; v < NUM_VIEWS; v++) beforePanes[v] = splitPane[v];
            layout();
            for (int v = 0; v < NUM_VIEWS; v++) if (cam[v].valid) {
                Vec2 oldCenter = wasSplit ? beforePanes[v].center() : before.center();
                Vec2 newCenter = splitActive ? splitPane[v].center() : rCanvas.center();
                cam[v].pan += newCenter - oldCenter;
            }'''),
 ('''    for (int v = 0; v < NUM_VIEWS; v++) if (!cam[v].valid) fitView(v, rCanvas);

    ui.begin();
    if (!ui.editingText() && !ui.blocking()) { if (readOnly) handleViewerKeys(); else handleShortcuts(); }
    canvasInput();''','''    for (int v = 0; v < NUM_VIEWS; v++) if (!cam[v].valid) fitView(v, splitActive ? splitPane[v] : rCanvas);

    ui.begin();
    if (!ui.editingText() && !ui.blocking()) { if (readOnly) handleViewerKeys(); else handleShortcuts(); }
    if (splitActive && in.pressed && drag == DRAG_NONE && !ui.blocking() && !ui.overBlocking(in.mouse)) {
        for (int v = 0; v < NUM_VIEWS; v++) if (splitPane[v].contains(in.mouse)) { setView(v); break; }
    }
    canvasInput();'''),
 ('''    drawCanvas(view, cam[view], rCanvas, false);
    drawCanvasOverlay();''','''    if (splitActive) {
        const char* labels[] = {"Breadboard", "Schematic", "PCB"};
        Hit activeHover = hover;
        DragMode activeDrag = drag;
        for (int v = 0; v < NUM_VIEWS; v++) {
            if (v != view) { hover = Hit{}; drag = DRAG_NONE; }
            else { hover = activeHover; drag = activeDrag; }
            drawCanvas(v, cam[v], splitPane[v], false);
            g.strokeRect(splitPane[v], (v == view ? 3.f : 1.f) * ui.s, v == view ? rgba(30, 118, 210) : rgba(140, 150, 165));
            Rect label(splitPane[v].x + 8 * ui.s, splitPane[v].y + 8 * ui.s, 114 * ui.s, 24 * ui.s);
            g.fillRoundRect(label, 5 * ui.s, rgba(245, 247, 250, 225));
            g.text(label.center(), labels[v], 12 * ui.s, rgba(35, 45, 60), 1);
        }
        hover = activeHover; drag = activeDrag;
    } else drawCanvas(view, cam[view], rCanvas, false);
    drawCanvasOverlay();''')])
patch('src/web.cpp','09193dd1363902347400d32f90455ca8b9627dbbd11b65000beabf99b538758d',[
 ('''extern "C" EMSCRIPTEN_KEEPALIVE int de_web_revision() {''','''extern "C" EMSCRIPTEN_KEEPALIVE int de_web_split(int enabled) {
    if (!g_webApp) return 0;
    g_webApp->splitRequested = enabled != 0;
    return 1;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_split_active() {
    return g_webApp && g_webApp->splitActive ? 1 : 0;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_view() {
    return g_webApp ? g_webApp->view : -1;
}
extern "C" EMSCRIPTEN_KEEPALIVE int de_web_revision() {''')])
patch('CMakeLists.txt','7b451416cbf4fe5e5cf10b6c2462e39cb80350855f6e098a8d3708b6edb99529',[
 ("'_de_web_revision','_de_web_snapshot'", "'_de_web_revision','_de_web_split','_de_web_split_active','_de_web_view','_de_web_snapshot'")])
print('Applied shared-document three-view patch')
