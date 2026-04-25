# N-Body Problem — Solar System Simulation

A numerical simulation of the solar system using the Velocity Verlet integrator. Bodies are configured in a single JSON file and results are rendered as an interactive animated plot.

## How it works

1. `config.json` defines all bodies — initial positions, velocities, masses, and visual properties.
2. CMake auto-generates `config.h` from `config.json` before each build via `generate_config.py`.
3. The C simulation runs the Velocity Verlet integrator and writes trajectory data to `data.csv`.
4. `visualization.py` reads `data.csv` and `config.json` and renders an animated 2D plot with scroll-to-zoom.

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
cmake -B cmake-build-debug -DCMAKE_BUILD_TYPE=Debug
cmake --build cmake-build-debug
```

`config.h` is generated automatically — do not edit it by hand.

## Usage

**Step 1 — Run the simulation**

Run the executable from the **project root** so it can find `config.json` and write `data.csv` next to it.

```bash
./cmake-build-debug/n_body_problem
```

The default configuration runs 100 000 steps of 1 day each (≈ 274 years). Progress is printed to stdout.

**Step 2 — Visualize**

```bash
python visualization.py
```

Scroll to zoom in/out. Orbits are shown relative to the Sun.

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
