#include <math.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <openblas/cblas.h>
#include "body.h"
#include "config.h"

#define CLR_RESET  "\033[0m"
#define CLR_BOLD   "\033[1m"
#define CLR_DIM    "\033[2m"
#define CLR_CYAN   "\033[36m"
#define CLR_GREEN  "\033[32m"
#define CLR_YELLOW "\033[33m"
#define CLR_GRAY   "\033[90m"

#define BAR_WIDTH 40
#define PROGRESS_INTERVAL 500

static void fmt_duration(double seconds, char *buf, size_t len) {
    int h  = (int)(seconds / 3600);
    int m  = (int)((seconds - h * 3600.0) / 60);
    int s  = (int)seconds % 60;
    int ms = (int)((seconds - (int)seconds) * 1000);
    snprintf(buf, len, "%02d:%02d:%02d.%03d", h, m, s, ms);
}

void init_bodies(Body system[N_BODIES]) {
    printf(CLR_BOLD "  Bodies\n" CLR_RESET);
    printf(CLR_GRAY "  ──────────────────────────────────────────────────\n" CLR_RESET);
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

        printf("  " CLR_CYAN "●" CLR_RESET "  %-24s  " CLR_GRAY "%.3e kg\n" CLR_RESET,
               system[i].name, system[i].m);
    }
    printf(CLR_GRAY "  ──────────────────────────────────────────────────\n" CLR_RESET);
    printf("  " CLR_GREEN CLR_BOLD "%d bodies loaded\n\n" CLR_RESET, N_BODIES);
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
        fprintf(file, "%s,%lf,%lf,%lf,%i\n",
                system[i].name, system[i].r[0], system[i].r[1], system[i].r[2], run);
    fclose(file);
}

static void print_progress(int t, clock_t start) {
    if (t % PROGRESS_INTERVAL != 0 && t != T_STEPS - 1)
        return;

    double pct     = (double)(t + 1) / T_STEPS;
    int    filled  = (int)(pct * BAR_WIDTH);
    double elapsed = (double)(clock() - start) / CLOCKS_PER_SEC;
    double rate    = (t + 1) / (elapsed > 0.0 ? elapsed : 1e-9);
    double eta     = (T_STEPS - t - 1) / rate;

    char eta_buf[16], elapsed_buf[16];
    fmt_duration(eta,     eta_buf,     sizeof(eta_buf));
    fmt_duration(elapsed, elapsed_buf, sizeof(elapsed_buf));

    printf("\r  " CLR_CYAN "[");
    for (int i = 0; i < BAR_WIDTH; i++)
        printf("%s", i < filled ? "█" : "░");
    printf("]" CLR_RESET
           "  " CLR_BOLD "%5.1f%%" CLR_RESET
           "   " CLR_GRAY "step %7d / %d" CLR_RESET
           "   " CLR_YELLOW "ETA %s" CLR_RESET
           "  elapsed %s  ",
           pct * 100.0, t + 1, T_STEPS, eta_buf, elapsed_buf);
    fflush(stdout);
}

int main(void) {
    printf("\n");
    printf(CLR_CYAN CLR_BOLD "  ╔════════════════════════════════════════════════╗\n" CLR_RESET);
    printf(CLR_CYAN CLR_BOLD "  ║      N-BODY SOLAR SYSTEM SIMULATION           ║\n" CLR_RESET);
    printf(CLR_CYAN CLR_BOLD "  ╚════════════════════════════════════════════════╝\n" CLR_RESET);
    printf("\n");

    Body system[N_BODIES];
    init_bodies(system);

    double sim_years = (double)T_STEPS * DT / (365.25 * 86400.0);
    printf(CLR_BOLD "  Simulation\n" CLR_RESET);
    printf(CLR_GRAY "  ──────────────────────────────────────────────────\n" CLR_RESET);
    printf("  Steps     " CLR_YELLOW "%d" CLR_RESET "  ×  " CLR_YELLOW "%.0f s" CLR_RESET "\n", T_STEPS, DT);
    printf("  Duration  " CLR_YELLOW "%.2f years\n\n" CLR_RESET, sim_years);

    calculate_accelerations(system);

    printf(CLR_BOLD "  Running\n" CLR_RESET);
    printf(CLR_GRAY "  ──────────────────────────────────────────────────\n" CLR_RESET);

    clock_t start = clock();

    for (int t = 0; t < T_STEPS; t++) {
        calculate_positions(system, DT);
        calculate_velocities(system, DT);
        calculate_accelerations(system);
        calculate_velocities(system, DT);
        write_positions(system, t);
        print_progress(t, start);
    }

    double total = (double)(clock() - start) / CLOCKS_PER_SEC;
    char total_buf[16];
    fmt_duration(total, total_buf, sizeof(total_buf));

    printf("\n\n");
    printf("  " CLR_GREEN CLR_BOLD "✓  Done" CLR_RESET
           "  in " CLR_BOLD "%s" CLR_RESET
           "  →  " CLR_CYAN "data.csv\n\n" CLR_RESET, total_buf);

    return 0;
}
