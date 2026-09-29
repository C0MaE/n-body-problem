"""Exports data.csv into web/data.js for the Three.js viewer in web/index.html.

Positions are downsampled to at most --max-frames frames, made Sun-relative,
converted to AU, rotated into the invariable plane (total angular momentum
along +z, so the view looks "down" on the solar system) and stored as a
base64 Float32Array. The result works from file:// or any static host
(GitHub Pages, Netlify, …).
"""
import argparse
import base64
import json
import math
import os
import numpy as np
import pandas as pd

# ─── ANSI Colors ──────────────────────────────────────────────────────────────

CLR_RESET  = "\033[0m"
CLR_BOLD   = "\033[1m"
CLR_CYAN   = "\033[36m"
CLR_GREEN  = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_GRAY   = "\033[90m"

_SEP = CLR_GRAY + "  " + "─" * 50 + CLR_RESET

AU      = 1.495978707e11   # m
G       = 6.673e-11        # same constant as main.c
YEAR    = 365.25 * 86400.0
HILL_K  = 1.0              # multiples of the Hill radius that still count as "orbiting"
ALIAS_FRAMES = 6           # moons with fewer frames per orbit are drawn as a ring

# North pole (RA, Dec in degrees, ICRF) for bodies drawn with rings.
POLES = {'saturn barycenter': (40.589, 83.537)}

# Display names for the SPICE body names used in config.json.
LABELS = {
    'jupiter barycenter': 'Jupiter', 'saturn barycenter': 'Saturn',
    'uranus barycenter': 'Uranus', 'neptune barycenter': 'Neptune',
    'pluto barycenter': 'Pluto',
}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data',       default='data.csv',    help='simulation output (default: data.csv)')
    p.add_argument('--config',     default='config.json', help='body config (default: config.json)')
    p.add_argument('--out',        default='web/data.js', help='output file (default: web/data.js)')
    p.add_argument('--max-frames', type=int,   default=16000, help='frames kept in the export (default: 16000)')
    p.add_argument('--start',      type=float, default=0.0,   help='window start in years (default: 0)')
    p.add_argument('--years',      type=float, default=None,  help='window length in years (default: whole run). '
                                                                   'Short windows give fast moons a smooth orbit.')
    p.add_argument('--epoch',      default=None, help='ISO date of step 0, e.g. 2026-04-25 '
                                                      '(default: simulation.epoch from config.json)')
    return p.parse_args()


def last_run(path):
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - 4096))
        tail = f.read().decode().strip().splitlines()
    return int(tail[-1].rsplit(',', 1)[1])


def invariable_plane_rotation(bodies):
    """Rotation matrix that maps the total angular momentum vector onto +z."""
    L = np.zeros(3)
    for b in bodies:
        L += b['mass'] * np.cross(b['r'], b['v'])
    z = L / np.linalg.norm(L)
    # Keep the x axis close to the original (equatorial) x axis.
    x = np.array([1.0, 0.0, 0.0]) - z[0] * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.vstack([x, y, z])


def find_parents(bodies):
    """Index of the body each body orbits (-1 for the Sun), via Hill spheres."""
    sun = next(i for i, b in enumerate(bodies) if b['name'] == 'sun')
    m_sun = bodies[sun]['mass']
    parents = []
    for i, b in enumerate(bodies):
        best = -1 if i == sun else sun
        best_d = math.inf
        for j, p in enumerate(bodies):
            if j in (i, sun) or p['mass'] < 50 * b['mass']:
                continue
            a = np.linalg.norm(np.array(p['r']) - np.array(bodies[sun]['r']))
            hill = a * (p['mass'] / (3 * m_sun)) ** (1 / 3)
            d = np.linalg.norm(np.array(b['r']) - np.array(p['r']))
            if d < HILL_K * hill and d < best_d:
                best, best_d = j, d
        parents.append(best)
    return parents


def main():
    args = parse_args()

    print()
    print(CLR_CYAN + CLR_BOLD + "  ╔════════════════════════════════════════════════╗" + CLR_RESET)
    print(CLR_CYAN + CLR_BOLD + "  ║                   WEB EXPORT                   ║" + CLR_RESET)
    print(CLR_CYAN + CLR_BOLD + "  ╚════════════════════════════════════════════════╝" + CLR_RESET)
    print()

    # ─── Config ───────────────────────────────────────────────────────────────

    with open(args.config) as f:
        cfg = json.load(f)
    bodies = cfg['bodies']
    names  = [b['name'] for b in bodies]
    n      = len(bodies)
    dt     = float(cfg['simulation']['dt'])
    epoch  = args.epoch or cfg['simulation'].get('epoch')

    # ─── Window ───────────────────────────────────────────────────────────────

    n_steps = last_run(args.data) + 1
    start   = min(n_steps - 1, int(round(args.start * YEAR / dt)))
    end     = n_steps if args.years is None else min(n_steps, start + int(round(args.years * YEAR / dt)))
    stride  = max(1, math.ceil((end - start) / args.max_frames))

    print(CLR_BOLD + "  Window" + CLR_RESET)
    print(_SEP)
    print(f"  {CLR_CYAN}●{CLR_RESET}  Steps       {CLR_YELLOW}{start} – {end - 1}{CLR_RESET}  {CLR_GRAY}of {n_steps}{CLR_RESET}")
    print(f"  {CLR_CYAN}●{CLR_RESET}  Duration    {CLR_YELLOW}{(end - start) * dt / YEAR:.2f} yr{CLR_RESET}")
    print(f"  {CLR_CYAN}●{CLR_RESET}  Frame step  {CLR_YELLOW}{stride} steps{CLR_RESET}  {CLR_GRAY}= {stride * dt / 3600:.1f} h per frame{CLR_RESET}")
    print(_SEP)
    print()

    # ─── Data (chunked, keeps only the sampled steps) ─────────────────────────

    print(CLR_BOLD + "  Data" + CLR_RESET)
    print(_SEP)

    head = pd.read_csv(args.data, nrows=n)['object'].tolist()
    if head != names:
        raise SystemExit(f"  {CLR_YELLOW}!{CLR_RESET}  {args.data} does not match {args.config} — rerun the simulation.")

    parts = []
    rows_read = 0
    chunk_rows = n * 50000
    for chunk in pd.read_csv(args.data, usecols=['rx', 'ry', 'rz', 'run'], chunksize=chunk_rows,
                             dtype={'rx': np.float64, 'ry': np.float64, 'rz': np.float64, 'run': np.int64}):
        rows_read += len(chunk)
        run = chunk['run'].to_numpy()
        keep = (run >= start) & (run < end) & ((run - start) % stride == 0)
        if keep.any():
            parts.append(chunk.loc[keep, ['rx', 'ry', 'rz']].to_numpy())
        pct = rows_read / (n_steps * n) * 100
        print(f"\r  {CLR_CYAN}●{CLR_RESET}  {args.data:<14}  {CLR_GRAY}{pct:5.1f} % read{CLR_RESET}", end='', flush=True)
        if run[-1] >= end:
            break

    pos = np.concatenate(parts).reshape(-1, n, 3)
    frames = pos.shape[0]
    print(f"\r  {CLR_CYAN}●{CLR_RESET}  {args.data:<14}  {CLR_GRAY}{frames} frames × {n} bodies{CLR_RESET}      ")

    sun = names.index('sun')
    pos = pos - pos[:, sun:sun + 1, :]
    rot = invariable_plane_rotation(bodies)
    pos = pos @ rot.T / AU
    print(f"  {CLR_CYAN}●{CLR_RESET}  Frame         {CLR_GRAY}Sun-centred, invariable plane, AU{CLR_RESET}")
    print(_SEP)
    print()

    # ─── Bodies ───────────────────────────────────────────────────────────────

    print(CLR_BOLD + "  Bodies" + CLR_RESET)
    print(_SEP)
    parents = find_parents(bodies)
    frame_dt = stride * dt
    out_bodies = []
    for i, b in enumerate(bodies):
        par = parents[i]
        if par < 0:
            period = 0.0
        else:
            rel = pos[:, i] - pos[:, par]
            a = float(np.mean(np.linalg.norm(rel, axis=1))) * AU
            period = 2 * math.pi * math.sqrt(a ** 3 / (G * (bodies[par]['mass'] + b['mass'])))
        label = LABELS.get(b['name'], b['name'].title())
        extra = {}
        if b['name'] in POLES:
            ra, dec = map(math.radians, POLES[b['name']])
            pole = np.array([math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)])
            extra['pole'] = (rot @ pole).round(6).tolist()
        if par >= 0 and 0 < period / frame_dt < ALIAS_FRAMES:
            # Too fast to animate at this frame rate: describe the orbit as a ring instead.
            rel = pos[:, i] - pos[:, par]
            normal = np.linalg.svd(rel - rel.mean(axis=0), full_matrices=False)[2][-1]
            if normal[2] < 0:
                normal = -normal
            extra['ring'] = {'r': float(np.mean(np.linalg.norm(rel, axis=1))), 'n': normal.round(6).tolist()}
        out_bodies.append({
            'name':   b['name'],
            'label':  label,
            'color':  b.get('color', '#FFFFFF'),
            'mass':   b['mass'],
            'radius': b.get('radius', 0.0) / AU,
            'parent': par,
            'period': period / frame_dt,   # in frames
            **extra,
        })
        role = 'star' if par < 0 else ('planet' if par == sun else f'moon of {LABELS.get(names[par], names[par].title())}')
        per = f"{period / 86400:9.2f} d" if period else "         —"
        warn = f"  {CLR_YELLOW}aliased{CLR_RESET}" if 'ring' in extra else ""
        print(f"  {CLR_CYAN}●{CLR_RESET}  {label:<10} {CLR_GRAY}{role:<18}{per}{CLR_RESET}{warn}")
    print(_SEP)
    print()

    # ─── Write ────────────────────────────────────────────────────────────────

    payload = {
        'version':  1,
        'frames':   frames,
        'frameDt':  frame_dt,
        'startT':   start * dt,
        'dt':       dt,
        'epoch':    epoch,
        'integrator': 'Velocity Verlet',
        'bodies':   out_bodies,
        'positions': base64.b64encode(pos.astype('<f4').tobytes()).decode(),
    }
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w') as f:
        f.write('// Generated by export_web.py — do not edit by hand.\n')
        f.write('window.NBODY_DATA = ')
        json.dump(payload, f, separators=(',', ':'))
        f.write(';\n')

    size_mb = os.path.getsize(args.out) / 1e6
    print(f"  {CLR_GREEN}{CLR_BOLD}✓  Done{CLR_RESET}  →  {CLR_CYAN}{args.out}{CLR_RESET}  {CLR_GRAY}({size_mb:.1f} MB){CLR_RESET}")
    print(f"     {CLR_GRAY}open web/index.html in a browser{CLR_RESET}\n")


if __name__ == '__main__':
    main()
