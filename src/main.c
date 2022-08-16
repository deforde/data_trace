#include <stdio.h>
#include <math.h>
#include <string.h>

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

void func(size_t len, float data1[len], float data2[len]) {
  memcpy(data2, data1, len * sizeof(*data1));
  printf("%s", "");
}

int main() {
  float arr[N_SAMPLES] = {0};
  float arr2[N_SAMPLES] = {0};
  my_struct_t s = {0};

  for (size_t n = 0; n < N_SAMPLES; ++n) {
    x = sinf(2 * M_PI * f * n * t_inc_s);
    w = x;
    s.a = x;
    arr[n] = x;
  }

  for (size_t n = 0; n < N_SAMPLES; ++n) {
    __attribute__((unused)) float *p = NULL;
    __attribute__((unused)) float y = cosf(2 * M_PI * f * n * t_inc_s);
    p = &y;
    s.b = y;
  }

  func(N_SAMPLES, arr, arr2);

  return 0;
}
