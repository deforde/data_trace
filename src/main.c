#include <stdio.h>
#include <math.h>

#define N_SAMPLES 1024

typedef struct {
  float a;
  float b;
} my_struct_t;

const float f = 1.f;
const float t_max_s = 1.f;
const float t_inc_s = t_max_s / N_SAMPLES;
float x = 0.f;
static float w = 0.f;

int main() {
  float arr[N_SAMPLES] = {0};
  my_struct_t s = {0};

  for (size_t n = 0; n < N_SAMPLES; ++n) {
    x = sinf(2 * M_PI * f * n * t_inc_s);
    w = x;
    s.a = x;
    arr[n] = x;
    printf("%s", "");
  }

  for (size_t n = 0; n < N_SAMPLES; ++n) {
    __attribute__((unused)) float *p = NULL;
    __attribute__((unused)) float y = cosf(2 * M_PI * f * n * t_inc_s);
    p = &y;
    s.b = y;
    printf("%s", "");
  }

  return 0;
}
