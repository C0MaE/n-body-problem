from skyfield.api import Loader
import json
import os

# ─── ANSI Colors ──────────────────────────────────────────────────────────────

CLR_RESET  = "\033[0m"
CLR_BOLD   = "\033[1m"
CLR_CYAN   = "\033[36m"
CLR_GREEN  = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_GRAY   = "\033[90m"

_SEP = CLR_GRAY + "  " + "─" * 50 + CLR_RESET

# ─── Header ───────────────────────────────────────────────────────────────────

print()
print(CLR_CYAN + CLR_BOLD + "  ╔════════════════════════════════════════════════╗" + CLR_RESET)
print(CLR_CYAN + CLR_BOLD + "  ║         PLANET DATA FETCHER                    ║" + CLR_RESET)
print(CLR_CYAN + CLR_BOLD + "  ╚════════════════════════════════════════════════╝" + CLR_RESET)
print()

# ─── Ephemeris ────────────────────────────────────────────────────────────────

print(CLR_BOLD + "  Ephemeris" + CLR_RESET)
print(_SEP)

load = Loader('./data')
ts   = load.timescale()
t    = ts.now()

_KERNELS = [
    ('de421.bsp',        'planets + Moon + Pluto'),
    ('jup365.bsp',       'Jupiter moons'),
    ('sat459.bsp',       'Saturn moons'),
    ('mar099.bsp',       'Mars moons'),
    ('ura111xl-799.bsp', 'Uranus moons'),
    ('nep105.bsp',       'Neptune moons'),
]

kernels = []
for _fname, _desc in _KERNELS:
    print(f"  {CLR_CYAN}●{CLR_RESET}  {_fname:<22}  {CLR_GRAY}loading…{CLR_RESET}", end='', flush=True)
    kernels.append(load(_fname))
    print(f"\r  {CLR_CYAN}●{CLR_RESET}  {_fname:<22}  {CLR_GRAY}{_desc}{CLR_RESET}          ")

print(_SEP)
print(f"  {CLR_GREEN}{CLR_BOLD}{len(kernels)} kernels loaded\n{CLR_RESET}")

sun_state = kernels[0]['sun'].at(t)

# ─── Body definitions ────────────────────────────────────────────────────────

BODIES = {
    'sun':                {'mass': 1.9885e30,  'radius': 6.9634e8},
    'mercury':            {'mass': 3.3011e23,  'radius': 2.4397e6},
    'venus':              {'mass': 4.8675e24,  'radius': 6.0518e6},
    'earth':              {'mass': 5.9724e24,  'radius': 6.3710e6},
    'moon':               {'mass': 7.342e22,   'radius': 1.7371e6},
    'mars':               {'mass': 6.4171e23,  'radius': 3.3895e6},
    'phobos':             {'mass': 1.0659e16,  'radius': 1.1260e4},
    'deimos':             {'mass': 1.4762e15,  'radius': 6.2000e3},
    'jupiter barycenter': {'mass': 1.8982e27,  'radius': 6.9911e7},
    'io':                 {'mass': 8.9319e22,  'radius': 1.8216e6},
    'europa':             {'mass': 4.7998e22,  'radius': 1.5608e6},
    'ganymede':           {'mass': 1.4819e23,  'radius': 2.6341e6},
    'callisto':           {'mass': 1.0759e23,  'radius': 2.4103e6},
    'saturn barycenter':  {'mass': 5.6834e26,  'radius': 5.8232e7},
    'mimas':              {'mass': 3.7493e19,  'radius': 1.9820e5},
    'enceladus':          {'mass': 1.0802e20,  'radius': 2.5210e5},
    'tethys':             {'mass': 6.1744e20,  'radius': 5.3110e5},
    'dione':              {'mass': 1.0954e21,  'radius': 5.6140e5},
    'rhea':               {'mass': 2.3065e21,  'radius': 7.6380e5},
    'titan':              {'mass': 1.3452e23,  'radius': 2.5747e6},
    'iapetus':            {'mass': 1.8056e21,  'radius': 7.3450e5},
    'uranus barycenter':  {'mass': 8.6810e25,  'radius': 2.5362e7},
    'ariel':              {'mass': 1.3530e21,  'radius': 5.7890e5},
    'umbriel':            {'mass': 1.2750e21,  'radius': 5.8470e5},
    'titania':            {'mass': 3.4000e21,  'radius': 7.8840e5},
    'oberon':             {'mass': 3.0760e21,  'radius': 7.6140e5},
    'miranda':            {'mass': 6.5900e19,  'radius': 2.3580e5},
    'neptune barycenter': {'mass': 1.0241e26,  'radius': 2.4622e7},
    'triton':             {'mass': 2.1390e22,  'radius': 1.3534e6},
    'pluto barycenter':   {'mass': 1.3030e22,  'radius': 1.1880e6},
}

CUSTOM_COLORS = {
    'sun': '#FDB813', 'mercury': '#B5B5B5', 'venus': '#E8C07D', 'earth': '#4BA3C3',
    'moon': '#D3D3D3', 'mars': '#C1440E', 'jupiter barycenter': '#C88B3A',
    'saturn barycenter': '#E4D191', 'uranus barycenter': '#7DE8E8',
    'neptune barycenter': '#5B5DDF', 'pluto barycenter': '#E3DCCB',
    'phobos': '#8A7A6B', 'deimos': '#A19485', 'io': '#E0C838', 'europa': '#A88D71',
    'ganymede': '#8C7C6D', 'callisto': '#635B51', 'mimas': '#D1E0E0',
    'enceladus': '#E6FFFF', 'tethys': '#C2D1D1', 'dione': '#A3B2B2',
    'rhea': '#8A9999', 'titan': '#F2A900', 'iapetus': '#5C4A3D',
    'ariel': '#B3C2B3', 'umbriel': '#7A8A7A', 'titania': '#D1E0D1',
    'oberon': '#5C6B5C', 'miranda': '#94A394', 'triton': '#FFC2B3'
}

DEFAULT_VISUALS = {'color': '#FFFFFF', 'marker_size': 5, 'trail_width': 0.7, 'trail_alpha': 0.6}
KM_TO_M = 1e3

# ─── Config Loading ──────────────────────────────────────────────────────────

config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file) as f:
        config = json.load(f)
else:
    config = {"simulation": {"t_steps": 500000, "dt": 3600}, "bodies": []}

existing = {b['name']: b for b in config.get('bodies', [])}

# ─── Data Extraction ─────────────────────────────────────────────────────────

print(CLR_BOLD + "  Bodies" + CLR_RESET)
print(_SEP)

updated = []

for name, props in BODIES.items():
    if name == 'sun':
        r, v = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    else:
        body = None
        for k in kernels:
            if name in k:
                body = k[name]
                break

        if body is None:
            print(f"  {CLR_YELLOW}!{CLR_RESET}  {name:<28}  {CLR_GRAY}not found — skipped{CLR_RESET}")
            continue

        state   = body.at(t)
        rel_pos = (state.position.km    - sun_state.position.km)    * KM_TO_M
        rel_vel = (state.velocity.km_per_s - sun_state.velocity.km_per_s) * KM_TO_M
        r, v    = rel_pos.tolist(), rel_vel.tolist()

    print(f"  {CLR_CYAN}●{CLR_RESET}  {name:<28}  {CLR_GRAY}{props['mass']:.3e} kg{CLR_RESET}")

    prev    = existing.get(name, {})
    visuals = {k: prev[k] for k in ('color', 'marker_size', 'trail_width', 'trail_alpha') if k in prev}

    if not visuals:
        visuals = DEFAULT_VISUALS.copy()
        if name in CUSTOM_COLORS:
            visuals['color'] = CUSTOM_COLORS[name]

        if 'barycenter' in name and name != 'pluto barycenter':
            visuals['marker_size'] = 7
        elif name in ['mercury', 'venus', 'earth', 'mars']:
            visuals['marker_size'] = 5
        else:
            visuals.update({'marker_size': 2, 'trail_width': 0.3, 'trail_alpha': 0.4})

    updated.append({
        'name': name, 'mass': props['mass'], 'radius': props['radius'],
        'r': r, 'v': v, **visuals
    })

print(_SEP)
print(f"  {CLR_GREEN}{CLR_BOLD}{len(updated)} bodies loaded\n{CLR_RESET}")

config['bodies'] = updated

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"  {CLR_GREEN}{CLR_BOLD}✓  Done{CLR_RESET}  →  {CLR_CYAN}{config_file}\n{CLR_RESET}")
