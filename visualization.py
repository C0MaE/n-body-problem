import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ─── Load body visual config from bodies.json ─────────────────────────────────

with open('config.json') as f:
    _bodies = json.load(f)['bodies']

BODY_CONFIG = {b['name']: b for b in _bodies}

# ─── Animation Configuration ──────────────────────────────────────────────────
# Visualization-only settings — these are not in bodies.json.

ANIMATION_CONFIG = {
    'data_file':    'data.csv',
    'frame_step':   10,       # steps skipped between animation frames (higher = faster playback)
    'interval_ms':  20,       # delay between frames in milliseconds
    'figure_size':  (10, 10),
    'zoom_scale':   1.2,      # scroll zoom factor (>1 zooms out on scroll-down)
    'initial_xlim': (-5e12, 5e12),  # meters — covers out to ~Neptune
    'initial_ylim': (-5e12, 5e12),
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
            'run': obj_data['run'].values,
        }

    sun_data = df[df['object'] == 'sun'].sort_values('run')
    sun_lookup = dict(zip(sun_data['run'], zip(sun_data['rx'], sun_data['ry'])))

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


def setup_plot(objects):
    cfg = ANIMATION_CONFIG
    fig, ax = plt.subplots(figsize=cfg['figure_size'], facecolor='black')
    ax.set_facecolor('black')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(*cfg['initial_xlim'])
    ax.set_ylim(*cfg['initial_ylim'])

    fallback_colors = plt.cm.plasma(np.linspace(0, 1, len(objects)))

    lines, points = {}, {}
    for i, name in enumerate(objects):
        v = _body_visual(name, fallback_colors[i])
        lines[name],  = ax.plot([], [], '-',  color=v['color'], linewidth=v['trail_width'], alpha=v['trail_alpha'])
        points[name], = ax.plot([], [], 'o',  color=v['color'], markersize=v['marker_size'], label=name)

    ax.legend(loc='upper right', fontsize='small', labelcolor='white')
    return fig, ax, lines, points


# ─── Interaction ──────────────────────────────────────────────────────────────

def make_zoom_handler(ax):
    scale = ANIMATION_CONFIG['zoom_scale']

    def zoom(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        factor = 1 / scale if event.button == 'up' else scale

        new_w = (cur_xlim[1] - cur_xlim[0]) * factor
        new_h = (cur_ylim[1] - cur_ylim[0]) * factor
        relx = (cur_xlim[1] - event.xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - event.ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([event.xdata - new_w * (1 - relx), event.xdata + new_w * relx])
        ax.set_ylim([event.ydata - new_h * (1 - rely), event.ydata + new_h * rely])
        ax.get_figure().canvas.draw_idle()

    return zoom


# ─── Animation ────────────────────────────────────────────────────────────────

def make_update(objects, data_dict, sun_lookup, lines, points):
    def update(frame):
        if frame not in sun_lookup:
            return []

        sun_x, sun_y = sun_lookup[frame]
        artists = []
        for name in objects:
            d = data_dict[name]
            mask = d['run'] <= frame
            rel_x = d['rx'][mask] - sun_x
            rel_y = d['ry'][mask] - sun_y

            if len(rel_x) > 0:
                lines[name].set_data(rel_x, rel_y)
                points[name].set_data([rel_x[-1]], [rel_y[-1]])

            artists.extend([lines[name], points[name]])
        return artists

    return update


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    cfg = ANIMATION_CONFIG
    objects, data_dict, sun_lookup = load_data(cfg['data_file'])
    n_steps = max(sun_lookup.keys())

    fig, ax, lines, points = setup_plot(objects)
    fig.canvas.mpl_connect('scroll_event', make_zoom_handler(ax))

    frame_step = max(1, min(cfg['frame_step'], n_steps // 500))

    update = make_update(objects, data_dict, sun_lookup, lines, points)
    ani = FuncAnimation(fig, update, frames=range(0, n_steps, frame_step),
                        interval=cfg['interval_ms'], blit=False)

    plt.show()
    return ani


if __name__ == '__main__':
    main()
