import json
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ─── ANSI Colors ──────────────────────────────────────────────────────────────

CLR_RESET  = "\033[0m"
CLR_BOLD   = "\033[1m"
CLR_CYAN   = "\033[36m"
CLR_GREEN  = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_GRAY   = "\033[90m"

_SEP = CLR_GRAY + "  " + "─" * 50 + CLR_RESET

# ─── Export config ────────────────────────────────────────────────────────────

DATA_FILE     = 'data.csv'
OUTPUT_FILE   = 'visualization.html'
MAX_FRAMES    = 400   # animation frames
TRAIL_PTS     = 600   # trail sample points per body
ORBIT_WINDOWS = 20    # how many Mercury orbital periods to show

# ─── Header ───────────────────────────────────────────────────────────────────

print()
print(CLR_CYAN + CLR_BOLD + "  ╔════════════════════════════════════════════════╗" + CLR_RESET)
print(CLR_CYAN + CLR_BOLD + "  ║         WEB EXPORT                             ║" + CLR_RESET)
print(CLR_CYAN + CLR_BOLD + "  ╚════════════════════════════════════════════════╝" + CLR_RESET)
print()

# ─── Load config ──────────────────────────────────────────────────────────────

print(CLR_BOLD + "  Config" + CLR_RESET)
print(_SEP)
with open('config.json') as f:
    _cfg = json.load(f)
BODY_CFG = {b['name']: b for b in _cfg['bodies']}
dt       = _cfg['simulation']['dt']
print(f"  {CLR_CYAN}●{CLR_RESET}  config.json   {CLR_GRAY}{len(BODY_CFG)} bodies, dt={dt} s{CLR_RESET}")
print(_SEP)
print()

# ─── Load data ────────────────────────────────────────────────────────────────

print(CLR_BOLD + "  Data" + CLR_RESET)
print(_SEP)
print(f"  {CLR_CYAN}●{CLR_RESET}  {DATA_FILE:<20}  {CLR_GRAY}loading…{CLR_RESET}", end='', flush=True)

df      = pd.read_csv(DATA_FILE)
objects = list(df['object'].unique())
n_steps = df['run'].nunique()

print(f"\r  {CLR_CYAN}●{CLR_RESET}  {DATA_FILE:<20}  {CLR_GRAY}{len(objects)} objects, {n_steps} steps{CLR_RESET}  ")

mercury_period_steps = max(1, int(88 * 24 * 3600 / dt))
orbit_window         = mercury_period_steps * ORBIT_WINDOWS
window_start         = max(0, n_steps - orbit_window)
window_steps         = n_steps - window_start
window_years         = window_steps * dt / (365.25 * 86400)
pts_per_orbit        = TRAIL_PTS / max(1, window_steps / mercury_period_steps)

print(f"  {CLR_CYAN}●{CLR_RESET}  Trail window  {CLR_GRAY}steps {window_start}–{n_steps-1}  ({window_years:.1f} yr){CLR_RESET}")
print(f"  {CLR_CYAN}●{CLR_RESET}  Mercury orbit {CLR_GRAY}{pts_per_orbit:.0f} pts/orbit{CLR_RESET}")

sun_df = df[df['object'] == 'sun'].sort_values('run').set_index('run')
data = {}
for name in objects:
    obj  = df[df['object'] == name].sort_values('run')
    runs = obj['run'].values
    data[name] = {
        'rx': obj['rx'].values - sun_df.loc[runs, 'rx'].values,
        'ry': obj['ry'].values - sun_df.loc[runs, 'ry'].values,
        'rz': obj['rz'].values - sun_df.loc[runs, 'rz'].values,
    }

print(_SEP)
print()

# ─── Build Plotly traces ──────────────────────────────────────────────────────

print(CLR_BOLD + "  Traces" + CLR_RESET)
print(_SEP)

trail_traces = []
dot_traces   = []

for name in objects:
    cfg   = BODY_CFG.get(name, {})
    color = cfg.get('color', '#FFFFFF')
    rx, ry, rz = data[name]['rx'], data[name]['ry'], data[name]['rz']

    idx = np.linspace(window_start, len(rx) - 1, min(TRAIL_PTS, window_steps), dtype=int)
    trail_traces.append(go.Scatter3d(
        x=rx[idx], y=ry[idx], z=rz[idx],
        mode='lines',
        name=name,
        showlegend=False,
        line=dict(color=color, width=max(0.5, cfg.get('trail_width', 0.7))),
        opacity=cfg.get('trail_alpha', 0.4),
        hoverinfo='none',
    ))

    raw_size = cfg.get('marker_size', 4)
    dot_traces.append(go.Scatter3d(
        x=[rx[window_start]], y=[ry[window_start]], z=[rz[window_start]],
        mode='markers',
        name=name,
        marker=dict(color=color, size=max(2, round(raw_size * 0.55)), line=dict(width=0)),
        hovertemplate=f'<b>{name}</b><extra></extra>',
    ))

    print(f"  {CLR_CYAN}●{CLR_RESET}  {name:<28}  {CLR_GRAY}{color}{CLR_RESET}")

print(_SEP)
print()

# ─── Plotly figure (no built-in animation controls) ───────────────────────────

lim = max(
    np.max(np.abs(data[name][ax]))
    for name in objects if name != 'sun'
    for ax in ('rx', 'ry', 'rz')
) * 1.05

fig = go.Figure(data=trail_traces + dot_traces)
fig.update_layout(
    paper_bgcolor='#000000',
    scene=dict(
        xaxis=dict(visible=False, range=[-lim, lim]),
        yaxis=dict(visible=False, range=[-lim, lim]),
        zaxis=dict(visible=False, range=[-lim, lim]),
        bgcolor='#000000',
        aspectmode='cube',
    ),
    legend=dict(font=dict(color='white', size=11), bgcolor='rgba(0,0,0,0)'),
    margin=dict(l=0, r=0, t=0, b=0),
)

# ─── JS animation data ────────────────────────────────────────────────────────

print(CLR_BOLD + "  Frames" + CLR_RESET)
print(_SEP)

frame_indices = np.linspace(window_start, n_steps - 1, min(MAX_FRAMES, window_steps), dtype=int)
n_frames      = len(frame_indices)
dot_indices   = list(range(len(objects), 2 * len(objects)))

frame_data_js = []
for fi, si in enumerate(frame_indices):
    frame_data_js.append({
        'x': [[float(data[name]['rx'][si])] for name in objects],
        'y': [[float(data[name]['ry'][si])] for name in objects],
        'z': [[float(data[name]['rz'][si])] for name in objects],
    })
    if (fi + 1) % 50 == 0 or fi == n_frames - 1:
        print(f"\r  {CLR_CYAN}●{CLR_RESET}  {fi + 1:>3} / {n_frames} frames  ", end='', flush=True)

print()
print(_SEP)
print()

# ─── Build and write HTML ─────────────────────────────────────────────────────

print(CLR_BOLD + "  Export" + CLR_RESET)
print(_SEP)
print(f"  {CLR_CYAN}●{CLR_RESET}  Writing {OUTPUT_FILE}…", end='', flush=True)

body_colors = {name: BODY_CFG.get(name, {}).get('color', '#FFFFFF') for name in objects}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>N-Body Solar System</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #000; overflow: hidden; font-family: 'Courier New', monospace; }
#plot { width: 100vw; height: 100vh; }

#panel {
    position: fixed;
    top: 16px;
    left: 16px;
    width: 226px;
    background: rgba(7,7,7,0.90);
    border: 1px solid #222;
    border-radius: 5px;
    padding: 13px 15px 11px;
    color: #ccc;
    font-size: 11px;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 999;
    user-select: none;
}

.p-title {
    color: #2dd9d9;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1.5px;
    margin-bottom: 11px;
}

hr.p-sep {
    border: none;
    border-top: 1px solid #1c1c1c;
    margin: 9px 0;
}

.p-row {
    display: flex;
    align-items: center;
    gap: 7px;
    margin: 7px 0;
}

.p-lbl { color: #555; min-width: 50px; flex-shrink: 0; }

.p-val { color: #ccc; min-width: 24px; text-align: right; font-size: 11px; }

#play-btn {
    background: #0e0e0e;
    border: 1px solid #2a2a2a;
    color: #2dd9d9;
    width: 30px;
    height: 22px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}
#play-btn:hover { border-color: #2dd9d9; background: #071212; }

input[type=range] {
    flex: 1;
    -webkit-appearance: none;
    appearance: none;
    height: 3px;
    border-radius: 2px;
    background: #222;
    outline: none;
    cursor: pointer;
}
input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #2dd9d9;
    cursor: pointer;
}
input[type=range]::-moz-range-thumb {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #2dd9d9;
    border: none;
    cursor: pointer;
}

#center-val {
    flex: 1;
    color: #2dd9d9;
    font-weight: bold;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
}

#time-val { color: #f0c040; font-size: 11px; }

.planets-grid { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 5px; }

.p-btn {
    border: 1px solid #252525;
    background: #0a0a0a;
    color: #505050;
    padding: 2px 5px;
    border-radius: 2px;
    cursor: pointer;
    font-size: 9.5px;
    font-family: 'Courier New', monospace;
    transition: border-color .1s, color .1s, background .1s;
    line-height: 1.5;
}
.p-btn:hover { color: #aaa; }
.p-btn.on { color: #2dd9d9; background: #041010; }

.zoom-btn {
    background: #0e0e0e;
    border: 1px solid #2a2a2a;
    color: #2dd9d9;
    width: 26px;
    height: 22px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 15px;
    font-family: monospace;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.zoom-btn:hover { border-color: #2dd9d9; background: #071212; }
</style>
</head>
<body>

<div id="plot"></div>

<div id="panel">
    <div class="p-title">N-BODY SIMULATION</div>

    <div class="p-row">
        <button id="play-btn" onclick="togglePlay()">&#9654;</button>
        <input id="scrubber" type="range" min="0" max="__N_FRAMES_MINUS_1__" value="0"
               oninput="onScrub(+this.value)">
    </div>
    <div class="p-row" style="margin-top:2px">
        <span class="p-lbl">Time</span>
        <span id="time-val">T + 0.00 yr</span>
    </div>

    <hr class="p-sep">

    <div class="p-row">
        <span class="p-lbl">Speed</span>
        <input id="speed-sl" type="range" min="0.5" max="8" value="3" step="0.5"
               oninput="onSpeedChange(+this.value)">
        <span class="p-val" id="speed-val">3&times;</span>
    </div>

    <hr class="p-sep">

    <div class="p-row">
        <span class="p-lbl">Zoom</span>
        <button class="zoom-btn" onclick="zoom(0.7)" title="Zoom in">+</button>
        <button class="zoom-btn" onclick="zoom(1/0.7)" title="Zoom out">&minus;</button>
        <button class="zoom-btn" onclick="zoom(0)" title="Reset zoom" style="width:auto;padding:0 6px;font-size:10px">&#8635;</button>
    </div>

    <hr class="p-sep">

    <div class="p-row">
        <span class="p-lbl">Center</span>
        <span id="center-val">&#8212;</span>
    </div>
    <div class="planets-grid" id="planet-btns"></div>
    <div style="color:#383838; font-size:9px; margin-top:6px">
        click planet button or dot to follow
    </div>
</div>

<script>
var FIG     = __FIG_JSON__;
var FRAMES  = __FRAME_DATA__;
var OBJECTS = __OBJECTS_JSON__;
var DOT_IDX = __DOT_IDX__;
var LIM     = __AXIS_LIM__;
var COLORS  = __BODY_COLORS__;
var N_FRAMES   = __N_FRAMES__;
var WINDOW_YRS = __WINDOW_YRS__;

var currentFrame    = 0;
var playing         = false;
var timer           = null;
var selectedPlanet  = null;
var currentHalfWidth = LIM;   // tracks zoom level (half axis span in world metres)

// ─── Init ────────────────────────────────────────────────────────────────────
Plotly.newPlot('plot', FIG.data, FIG.layout, {
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage'],
    responsive: true
});

// ─── Planet buttons ──────────────────────────────────────────────────────────
(function() {
    var grid = document.getElementById('planet-btns');
    OBJECTS.forEach(function(name) {
        var btn = document.createElement('button');
        btn.className = 'p-btn';
        btn.id = 'pb-' + name.replace(/ /g, '_');
        btn.textContent = name.replace(' barycenter', '');
        var c = COLORS[name] || '#ffffff';
        btn.style.borderColor = c + '50';
        btn.addEventListener('click', function() { selectPlanet(name); });
        grid.appendChild(btn);
    });
})();

// ─── Axis-range helpers ──────────────────────────────────────────────────────
function applyRanges(cx, cy, cz, hw) {
    Plotly.relayout('plot', {
        'scene.xaxis.range': [cx - hw, cx + hw],
        'scene.yaxis.range': [cy - hw, cy + hw],
        'scene.zaxis.range': [cz - hw, cz + hw]
    });
}

function resetRanges() {
    currentHalfWidth = LIM;
    applyRanges(0, 0, 0, LIM);
}

// ─── Render a frame ──────────────────────────────────────────────────────────
function renderFrame(idx) {
    var fd = FRAMES[idx];
    Plotly.restyle('plot', { x: fd.x, y: fd.y, z: fd.z }, DOT_IDX);

    if (selectedPlanet !== null) {
        var pi = OBJECTS.indexOf(selectedPlanet);
        if (pi >= 0) {
            applyRanges(fd.x[pi][0], fd.y[pi][0], fd.z[pi][0], currentHalfWidth);
        }
    }

    document.getElementById('scrubber').value = idx;
    var t = (idx / Math.max(1, N_FRAMES - 1)) * WINDOW_YRS;
    document.getElementById('time-val').textContent =
        'T + ' + t.toFixed(2) + ' yr';
}

// ─── Play / Pause ────────────────────────────────────────────────────────────
function getMs() {
    return Math.max(10, Math.round(120 / (+document.getElementById('speed-sl').value)));
}

function play() {
    if (timer) clearInterval(timer);
    timer = setInterval(function() {
        currentFrame = (currentFrame + 1) % N_FRAMES;
        renderFrame(currentFrame);
    }, getMs());
    playing = true;
    document.getElementById('play-btn').innerHTML = '&#9646;&#9646;';
}

function pause() {
    if (timer) { clearInterval(timer); timer = null; }
    playing = false;
    document.getElementById('play-btn').innerHTML = '&#9654;';
}

function togglePlay() { playing ? pause() : play(); }

// ─── Speed ───────────────────────────────────────────────────────────────────
function onSpeedChange(v) {
    var label = Number.isInteger(v) ? v + '×' : v.toFixed(1).replace('.0', '') + '×';
    document.getElementById('speed-val').textContent = label;
    if (playing) play();
}

// ─── Scrubber ────────────────────────────────────────────────────────────────
function onScrub(v) {
    pause();
    currentFrame = v;
    renderFrame(currentFrame);
}

// ─── Planet selection ────────────────────────────────────────────────────────
function selectPlanet(name) {
    if (selectedPlanet === name) {
        selectedPlanet = null;
        resetRanges();
        document.getElementById('center-val').innerHTML = '&#8212;';
    } else {
        selectedPlanet = name;
        document.getElementById('center-val').textContent = name;

        // Auto-zoom: fit the view to ~3× the planet's orbital radius from sun
        var pi = OBJECTS.indexOf(name);
        var fd = FRAMES[currentFrame];
        var px = fd.x[pi][0], py = fd.y[pi][0], pz = fd.z[pi][0];
        var orbitR = Math.sqrt(px * px + py * py + pz * pz);
        // Give at least LIM/80 so tiny-orbit moons are still visible
        currentHalfWidth = orbitR > 0 ? Math.max(orbitR * 3, LIM / 80) : LIM / 12;
        applyRanges(px, py, pz, currentHalfWidth);
    }
    OBJECTS.forEach(function(n) {
        var btn = document.getElementById('pb-' + n.replace(/ /g, '_'));
        if (btn) {
            btn.className = 'p-btn' + (n === selectedPlanet ? ' on' : '');
            var c = COLORS[n] || '#ffffff';
            btn.style.borderColor = n === selectedPlanet ? c : c + '50';
        }
    });
}

// ─── Zoom ────────────────────────────────────────────────────────────────────
function zoom(factor) {
    if (factor === 0) { resetRanges(); return; }

    currentHalfWidth *= factor;

    // Zoom around the current view centre (preserves any pan / planet follow)
    var gd     = document.getElementById('plot');
    var scene  = gd.layout.scene || {};
    var xr     = (scene.xaxis && scene.xaxis.range) || [-LIM, LIM];
    var yr     = (scene.yaxis && scene.yaxis.range) || [-LIM, LIM];
    var zr     = (scene.zaxis && scene.zaxis.range) || [-LIM, LIM];
    var cx     = (xr[0] + xr[1]) / 2;
    var cy     = (yr[0] + yr[1]) / 2;
    var cz     = (zr[0] + zr[1]) / 2;
    applyRanges(cx, cy, cz, currentHalfWidth);
}

// Click on dot or trail in the 3D plot
document.getElementById('plot').on('plotly_click', function(d) {
    if (!d || !d.points.length) return;
    selectPlanet(d.points[0].fullData.name);
});
</script>
</body>
</html>"""

html = (HTML
    .replace('__FIG_JSON__',       fig.to_json())
    .replace('__FRAME_DATA__',     json.dumps(frame_data_js, separators=(',', ':')))
    .replace('__OBJECTS_JSON__',   json.dumps(objects))
    .replace('__DOT_IDX__',        json.dumps(dot_indices))
    .replace('__AXIS_LIM__',       repr(float(lim)))
    .replace('__N_FRAMES__',       str(n_frames))
    .replace('__N_FRAMES_MINUS_1__', str(n_frames - 1))
    .replace('__WINDOW_YRS__',     f'{window_years:.4f}')
    .replace('__BODY_COLORS__',    json.dumps(body_colors)))

with open(OUTPUT_FILE, 'w') as f:
    f.write(html)

size_mb = os.path.getsize(OUTPUT_FILE) / 1e6
print(f"\r  {CLR_CYAN}●{CLR_RESET}  {OUTPUT_FILE:<30}  {CLR_GRAY}written{CLR_RESET}          ")
print(_SEP)
print(f"\n  {CLR_GREEN}{CLR_BOLD}✓  Done{CLR_RESET}  →  {CLR_CYAN}{OUTPUT_FILE}{CLR_RESET}  {CLR_GRAY}({size_mb:.1f} MB)\n{CLR_RESET}")
