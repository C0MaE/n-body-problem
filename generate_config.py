"""Generates config.h from config.json. Run automatically by CMake before each build."""
import json
import os

src_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(src_dir, 'config.json')) as f:
    cfg = json.load(f)

bodies = cfg['bodies']
sim = cfg['simulation']

lines = [
    '#ifndef CONFIG_H',
    '#define CONFIG_H',
    '',
    f'#define T_STEPS {sim["t_steps"]}',
    f'#define DT      {sim["dt"]}.0',
    '',
    'typedef struct {',
    '    const char *name;',
    '    double mass;',
    '    double radius;',
    '    double r[3];',
    '    double v[3];',
    '} BodyConfig;',
    '',
    '// Auto-generated from bodies.json — do not edit by hand.',
    'static const BodyConfig BODY_CONFIGS[] = {',
]

for b in bodies:
    r = b['r']
    v = b['v']
    lines.append(
        f'    {{ "{b["name"]}", {b["mass"]!r}, {b["radius"]!r},'
        f' {{{r[0]!r}, {r[1]!r}, {r[2]!r}}}, {{{v[0]!r}, {v[1]!r}, {v[2]!r}}} }},'
    )

lines += [
    '};',
    '',
    '#define N_BODIES ((int)(sizeof(BODY_CONFIGS) / sizeof(BODY_CONFIGS[0])))',
    '',
    '#endif',
    '',
]

out = os.path.join(src_dir, 'config.h')
with open(out, 'w') as f:
    f.write('\n'.join(lines))

print(f'Generated {out} with {len(bodies)} bodies.')
