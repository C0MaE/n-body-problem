#ifndef BODY_H
#define BODY_H

typedef struct {
    double r[3];
    double v[3];
    double a[3];
    double m;
    double radius;
    char name[49];
} Body;

#endif