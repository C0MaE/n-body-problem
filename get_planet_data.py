from skyfield.api import load
import csv

# Ephemeriden laden
planets = load('de421.bsp')
ts = load.timescale()
t = ts.now()

sun = planets['sun']

# Massen (kg)
planet_mass = {
    'sun': 1.9885e30,
    'mercury': 3.3011e23,
    'venus':   4.8675e24,
    'earth':   5.97237e24,
    'mars':    6.4171e23,
    'jupiter barycenter': 1.8982e27,
    'saturn barycenter':  5.6834e26,
    'uranus barycenter':  8.6810e25,
    'neptune barycenter': 1.02413e26,
}

# Radien (km) – mittlere IAU-Werte
planet_radius = {
    'sun': 696340,
    'mercury': 2439.7,
    'venus': 6051.8,
    'earth': 6371.0,
    'mars': 3389.5,
    'jupiter barycenter': 69911,
    'saturn barycenter': 58232,
    'uranus barycenter': 25362,
    'neptune barycenter': 24622,
}

with open('planet_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    writer.writerow([
        'body',
        'mass_kg',
        'radius_km',
        'x_km', 'y_km', 'z_km',
        'vx_km_s', 'vy_km_s', 'vz_km_s'
    ])

    for name, mass in planet_mass.items():

        radius = planet_radius.get(name, 0.0)

        if name == 'sun':
            pos = [0.0, 0.0, 0.0]
            vel = [0.0, 0.0, 0.0]
        else:
            body = planets[name]
            astrometric = sun.at(t).observe(body)
            pos = astrometric.position.km
            vel = astrometric.velocity.km_per_s

        writer.writerow([
            name,
            mass,
            radius,
            pos[0], pos[1], pos[2],
            vel[0], vel[1], vel[2]
        ])

print("Alle Planetendaten inkl. Radius wurden gespeichert.")