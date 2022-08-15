#include <stdio.h>
#include <math.h>

#define N_SAMPLES 1024

const float f = 1.f;
const float fs = 25.f;
__attribute__((unused)) float y = 0.f;

int main() {
  for (size_t n = 0; n < N_SAMPLES; ++n) {
    y = sinf(2 * M_PI * n * f / fs);
    // printf("%.2f%s", y, (n < N_SAMPLES - 1) ? ", " : "");
  }
  puts("");
  return 0;
}
