#include <math.h>
#include <stdio.h>
#include <string.h>
#include <openblas/cblas.h>
#include "body.h"
#include "config.h"

void init_bodies(Body system[N_BODIES]) {
    for (int i = 0; i < N_BODIES; i++) {
        strncpy(system[i].name, BODY_CONFIGS[i].name, sizeof(system[i].name) - 1);
        system[i].name[sizeof(system[i].name) - 1] = '\0';

        system[i].m      = BODY_CONFIGS[i].mass;
        system[i].radius = BODY_CONFIGS[i].radius;

        for (int d = 0; d < 3; d++) {
            system[i].r[d] = BODY_CONFIGS[i].r[d];
            system[i].v[d] = BODY_CONFIGS[i].v[d];
            system[i].a[d] = 0.0;
        }

        printf("loaded: %s\n", system[i].name);
    }
    printf("\nAll %d objects have been loaded.\n", N_BODIES);
}

void calculate_accelerations(Body system[N_BODIES]) {
    const double G = 6.673e-11;
    for (int i = 0; i < N_BODIES; i++) {
        system[i].a[0] = 0.0;
        system[i].a[1] = 0.0;
        system[i].a[2] = 0.0;
        for (int k = 0; k < N_BODIES; k++) {
            if (i != k) {
                double r[3] = {
                    system[k].r[0] - system[i].r[0],
                    system[k].r[1] - system[i].r[1],
                    system[k].r[2] - system[i].r[2]
                };
                double norm = cblas_dnrm2(3, r, 1);
                double factor = G * system[k].m / (norm * norm * norm);
                system[i].a[0] += factor * r[0];
                system[i].a[1] += factor * r[1];
                system[i].a[2] += factor * r[2];
            }
        }
    }
}

void calculate_positions(Body system[N_BODIES], double dt) {
    for (int i = 0; i < N_BODIES; i++) {
        system[i].r[0] += system[i].v[0] * dt + 0.5 * system[i].a[0] * dt * dt;
        system[i].r[1] += system[i].v[1] * dt + 0.5 * system[i].a[1] * dt * dt;
        system[i].r[2] += system[i].v[2] * dt + 0.5 * system[i].a[2] * dt * dt;
    }
}

void calculate_velocities(Body system[N_BODIES], double dt) {
    for (int i = 0; i < N_BODIES; i++) {
        system[i].v[0] += 0.5 * system[i].a[0] * dt;
        system[i].v[1] += 0.5 * system[i].a[1] * dt;
        system[i].v[2] += 0.5 * system[i].a[2] * dt;
    }
}

void write_positions(Body system[N_BODIES], int run) {
    const char *filename = "data.csv";

    FILE *file = fopen(filename, run == 0 ? "w" : "a");
    if (!file) {
        perror("Error opening output file");
        return;
    }

    if (run == 0)
        fprintf(file, "object,rx,ry,rz,run\n");

    for (int i = 0; i < N_BODIES; i++)
        fprintf(file, "%s,%lf,%lf,%lf,%i\n", system[i].name, system[i].r[0], system[i].r[1], system[i].r[2], run);

    fclose(file);
    printf("wrote step %d\n", run);
}

int main(void) {
    Body system[N_BODIES];
    init_bodies(system);

    calculate_accelerations(system);

    printf("start calculating\n");
    for (int t = 0; t < T_STEPS; t++) {
        calculate_positions(system, DT);
        calculate_velocities(system, DT);
        calculate_accelerations(system);
        calculate_velocities(system, DT);
        write_positions(system, t);
    }

    return 0;
}
