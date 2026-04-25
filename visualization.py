import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3d projection
from matplotlib.animation import FuncAnimation


# ─── Load body visual config ──────────────────────────────────────────────────

with open('config.json') as f:
    _bodies = json.load(f)['bodies']

BODY_CONFIG  = {b['name']: b            for b in _bodies}
BODY_RADII   = {b['name']: b.get('radius', 0.0) for b in _bodies}

# ─── Animation Configuration ──────────────────────────────────────────────────

ANIMATION_CONFIG = {
    'data_file':   'data.csv',
    'frame_step':  20,       # steps skipped between animation frames
    'interval_ms': 20,       # delay between frames in milliseconds
    'figure_size': (10, 10),
    'zoom_scale':  1.2,      # scroll zoom factor
    'initial_lim': 5e12,     # symmetric ± limit for all 3 axes (meters)
}


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_data(filepath: str):
    df = pd.read_csv(filepath)
    objects = df['object'].unique()

    data_dict = {}
    for name in objects:
        obj_data = df[df['object'] == name].sort_values('run')
        data_dict[name] = {
            'rx':  obj_data['rx'].values,
            'ry':  obj_data['ry'].values,
            'rz':  obj_data['rz'].values,
            'run': obj_data['run'].values,
        }

    sun_data = df[df['object'] == 'sun'].sort_values('run')
    sun_lookup = dict(zip(
        sun_data['run'],
        zip(sun_data['rx'], sun_data['ry'], sun_data['rz']),
    ))

    return objects, data_dict, sun_lookup


# ─── Plot Setup ───────────────────────────────────────────────────────────────

def _body_visual(name: str, fallback_color):
    cfg = BODY_CONFIG.get(name, {})
    return {
        'color':       cfg.get('color',       fallback_color),
        'marker_size': cfg.get('marker_size', 5),
        'trail_width': cfg.get('trail_width', 0.7),
        'trail_alpha': cfg.get('trail_alpha', 0.5),
    }


def compute_real_marker_sizes(ax, fig, objects):
    """Marker diameter in points = 2 * real_radius * (fig_width_pt / axis_range_m).
    Falls back to config marker_size for bodies with no radius data."""
    x_lo, x_hi = ax.get_xlim3d()
    axis_range  = x_hi - x_lo
    fig_width_pt = fig.get_figwidth() * 72  # inches → points
    sizes = {}
    for name in objects:
        radius = BODY_RADII.get(name, 0.0)
        if radius > 0 and axis_range > 0:
            diameter_pt = 2 * radius * fig_width_pt / axis_range
            sizes[name] = max(1.5, diameter_pt)
        else:
            sizes[name] = BODY_CONFIG.get(name, {}).get('marker_size', 5)
    return sizes


def setup_plot(objects):
    cfg = ANIMATION_CONFIG
    fig = plt.figure(figsize=cfg['figure_size'], facecolor='black')
    ax = fig.add_subplot(111, projection='3d')

    ax.set_facecolor('black')
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('none')
    ax.yaxis.pane.set_edgecolor('none')
    ax.zaxis.pane.set_edgecolor('none')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.grid(False)
    ax.set_proj_type('persp', focal_length=0.2)  # perspective depth cues
    ax.set_box_aspect([1, 1, 1])                 # keep visual box cubic with non-equal data ranges

    lim = cfg['initial_lim']
    ax.set_xlim3d(-lim, lim)
    ax.set_ylim3d(-lim, lim)
    ax.set_zlim3d(-lim, lim)

    fallback_colors = plt.cm.plasma(np.linspace(0, 1, len(objects)))

    lines, points = {}, {}
    for i, name in enumerate(objects):
        v = _body_visual(name, fallback_colors[i])
        lines[name],  = ax.plot([], [], [], '-', color=v['color'],
                                linewidth=v['trail_width'], alpha=v['trail_alpha'])
        points[name], = ax.plot([], [], [], 'o', color=v['color'],
                                markersize=v['marker_size'], label=name)

    ax.legend(loc='upper right', fontsize='small', labelcolor='white',
              facecolor='black', edgecolor='none')
    return fig, ax, lines, points


# ─── Interaction ──────────────────────────────────────────────────────────────

def make_zoom_handler(ax, fig, objects, points, state):
    scale = ANIMATION_CONFIG['zoom_scale']

    def zoom(event):
        factor = 1 / scale if event.button == 'up' else scale
        for get_lim, set_lim in [
            (ax.get_xlim3d, ax.set_xlim3d),
            (ax.get_ylim3d, ax.set_ylim3d),
            (ax.get_zlim3d, ax.set_zlim3d),
        ]:
            lo, hi = get_lim()
            mid = (lo + hi) / 2
            half = (hi - lo) / 2 * factor
            set_lim(mid - half, mid + half)
        sizes = compute_real_marker_sizes(ax, fig, objects)
        state['marker_sizes'] = sizes
        _apply_selection_highlight(objects, points, state['selected'], sizes)
        ax.get_figure().canvas.draw_idle()

    return zoom


def _apply_selection_highlight(objects, points, selected_name, current_sizes):
    for name in objects:
        base_size = current_sizes.get(name, BODY_CONFIG.get(name, {}).get('marker_size', 5))
        if name == selected_name:
            points[name].set_markersize(base_size * 2.5)
            points[name].set_markeredgecolor('white')
            points[name].set_markeredgewidth(1.5)
        else:
            points[name].set_markersize(base_size)
            points[name].set_markeredgecolor('none')


def make_click_handlers(ax, objects, points, state):
    """Returns (on_press, on_release) — split to distinguish clicks from rotation drags."""
    _press_xy = [None]
    DRAG_THRESHOLD = 5  # pixels

    def on_press(event):
        _press_xy[0] = (event.x, event.y)

    def on_release(event):
        if _press_xy[0] is None:
            return
        dx = abs(event.x - _press_xy[0][0])
        dy = abs(event.y - _press_xy[0][1])
        _press_xy[0] = None

        if dx > DRAG_THRESHOLD or dy > DRAG_THRESHOLD:
            return  # rotation drag — ignore

        if event.button == 3:
            state['selected'] = None
            _apply_selection_highlight(objects, points, None, state['marker_sizes'])
            ax.get_figure().canvas.draw_idle()
            return

        if event.button != 1:
            return

        for name in objects:
            hit, _ = points[name].contains(event)
            if hit:
                state['selected'] = None if state['selected'] == name else name
                _apply_selection_highlight(objects, points, state['selected'], state['marker_sizes'])
                ax.get_figure().canvas.draw_idle()
                return

        # Click in empty space deselects
        state['selected'] = None
        _apply_selection_highlight(objects, points, None, state['marker_sizes'])
        ax.get_figure().canvas.draw_idle()

    return on_press, on_release


# ─── Animation ────────────────────────────────────────────────────────────────

def make_update(objects, data_dict, sun_lookup, lines, points, ax, fig, state):
    def update(frame):
        state['frame'] = frame
        if frame not in sun_lookup:
            return []

        sun_x, sun_y, sun_z = sun_lookup[frame]
        selected_pos = None
        artists = []

        sizes = compute_real_marker_sizes(ax, fig, objects)
        state['marker_sizes'] = sizes

        for name in objects:
            d = data_dict[name]
            mask = d['run'] <= frame
            rel_x = d['rx'][mask] - sun_x
            rel_y = d['ry'][mask] - sun_y
            rel_z = d['rz'][mask] - sun_z

            if len(rel_x) > 0:
                lines[name].set_data(rel_x, rel_y)
                lines[name].set_3d_properties(rel_z)
                points[name].set_data([rel_x[-1]], [rel_y[-1]])
                points[name].set_3d_properties([rel_z[-1]])
                if name == state['selected']:
                    selected_pos = (rel_x[-1], rel_y[-1], rel_z[-1])

            artists.extend([lines[name], points[name]])

        _apply_selection_highlight(objects, points, state['selected'], sizes)

        if selected_pos is not None:
            cx, cy, cz = selected_pos
            for get_lim, set_lim, center in [
                (ax.get_xlim3d, ax.set_xlim3d, cx),
                (ax.get_ylim3d, ax.set_ylim3d, cy),
                (ax.get_zlim3d, ax.set_zlim3d, cz),
            ]:
                lo, hi = get_lim()
                half = (hi - lo) / 2
                set_lim(center - half, center + half)

        return artists

    return update


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    cfg = ANIMATION_CONFIG
    objects, data_dict, sun_lookup = load_data(cfg['data_file'])
    n_steps = max(sun_lookup.keys())

    fig, ax, lines, points = setup_plot(objects)

    initial_sizes = compute_real_marker_sizes(ax, fig, objects)
    state = {'selected': None, 'frame': 0, 'marker_sizes': initial_sizes}

    fig.canvas.mpl_connect('scroll_event', make_zoom_handler(ax, fig, objects, points, state))
    on_press, on_release = make_click_handlers(ax, objects, points, state)
    fig.canvas.mpl_connect('button_press_event', on_press)
    fig.canvas.mpl_connect('button_release_event', on_release)

    frame_step = max(1, min(cfg['frame_step'], n_steps // 500))

    update = make_update(objects, data_dict, sun_lookup, lines, points, ax, fig, state)
    ani = FuncAnimation(fig, update, frames=range(0, n_steps, frame_step),
                        interval=cfg['interval_ms'], blit=False)

    plt.show()
    return ani


if __name__ == '__main__':
    main()
