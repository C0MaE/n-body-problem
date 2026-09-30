# N-Body Problem — Solar System Simulation

**[▶ Open the web viewer](https://nbody.comae.dev/)**

A numerical simulation of the solar system using the Velocity Verlet integrator. Bodies are configured in a single JSON file and results are rendered as an interactive animated plot.

## How it works

1. `config.json` defines all bodies — initial positions, velocities, masses, and visual properties.
2. CMake auto-generates `config.h` from `config.json` before each build via `generate_config.py`.
3. The C simulation runs the Velocity Verlet integrator and writes trajectory data to `data.csv`.
4. `visualization.py` reads `data.csv` and `config.json` and renders an animated 3D plot with scroll-to-zoom.
5. `export_web.py` packs `data.csv` into `web/data.js` for the Three.js web viewer in `web/index.html`, which can also export MP4 videos.

## Dependencies

**C simulation**
- CMake ≥ 3.20
- Python 3 (for config generation at build time)
- OpenBLAS
- OpenMP

**Python scripts**
- `pandas`
- `matplotlib`
- `numpy`
- `skyfield` (only needed for `get_planet_data.py`)

```bash
pip install pandas matplotlib numpy skyfield
```

## Build

```bash
cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release
```

`config.h` is generated automatically — do not edit it by hand.

## Usage

**Step 1 — Run the simulation**

Run the executable from the **project root** so it can find `config.json` and write `data.csv` next to it.

```bash
./cmake-build-release/n_body_problem
```

The default configuration runs 100 000 steps of 1 day each (≈ 274 years). Progress is printed to stdout.

**Step 2 — Visualize**

```bash
python visualization.py
```

Scroll to zoom in/out. Orbits are shown relative to the Sun.

**Step 3 — Web viewer and video export**

```bash
python export_web.py --epoch 2026-04-25
python -m http.server --directory web 8000
```

Then open <http://localhost:8000>. Opening `web/index.html` directly from disk works as well. The `web/` folder is a static site, so you can host it anywhere (GitHub Pages, Netlify, …) as long as `data.js` sits next to `index.html`.

**Live version:** <https://nbody.comae.dev/>. Every push to `main` that touches `web/` redeploys it through `.github/workflows/pages.yml`. To publish a new run, re-export and commit `web/data.js`.

The export downsamples the run to at most 16 000 frames, puts the Sun at the origin and rotates everything into the invariable plane (total angular momentum along +z). Useful options:

| Option | Effect |
|---|---|
| `--epoch 2026-04-25` | Date of step 0, shown as a calendar date and Julian Date. Defaults to `simulation.epoch` in `config.json`, which `get_planet_data.py` now writes. |
| `--years 2` / `--start 10` | Export only a window of the run. A shorter window gives more frames per orbit, so fast moons such as Io or Phobos move smoothly instead of being drawn as a ring. |
| `--max-frames 16000` | Frame budget. Larger values mean a larger `data.js`. |

In the viewer, drag to rotate, scroll to zoom and click a body (or pick it in the list) to follow it. `#earth`, `#jupiter` etc. in the URL start focused on that body. Keyboard shortcuts: `Space` pause, `H` hide the UI, `R` record, `Esc` back to the Sun.

**Video:** *Video* renders an MP4 frame by frame (WebCodecs + mp4-muxer) in Full HD, 4K, 9:16 portrait or square, at 30 or 60 fps. It is not a screen capture, so the result is smooth regardless of how fast your machine is. Camera, focus and playback speed come from the current view, with an optional slow camera orbit and a date/scale overlay. This needs Chrome, Edge, Safari 17+ or Firefox 130+. *Bild* saves a PNG still.

## Units

All values throughout the simulation use SI units:

| Quantity | Unit |
|---|---|
| Position (`r`) | m — metres, Sun-relative |
| Velocity (`v`) | m/s |
| Mass | kg |
| Radius | m |
| Time step (`dt`) | s — seconds |

## Adding a body

Edit `config.json` and append an entry to the `"bodies"` array:

```json
{
  "name": "pluto", "mass": 1.303e22, "radius": 1188.3,
  "r": [x_km, y_km, z_km], "v": [vx_km_s, vy_km_s, vz_km_s],
  "color": "#A0A0A0", "marker_size": 3, "trail_width": 0.7, "trail_alpha": 0.6
}
```

All positions and velocities are Sun-relative. Current ephemeris values for any body can be obtained by adding it to `get_planet_data.py` and running:

```bash
python get_planet_data.py
```

Then rebuild — `config.h` is regenerated automatically.

## Configuration

| File | What to configure |
|---|---|
| `config.json` → `simulation` | Step count and time step size |
| `config.json` → `bodies` | Bodies, initial conditions, visual properties |
| `visualization.py` → `ANIMATION_CONFIG` | Playback speed, zoom, figure size |

To change the simulation duration or time step, edit the `simulation` block in `config.json`:

```json
"simulation": {
  "t_steps": 100000,
  "dt": 86400
}
```

`t_steps` is the number of integration steps, `dt` is the step size in seconds (86400 = 1 day). Rebuild after any changes.
