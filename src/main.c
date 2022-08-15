#include <stdio.h>
#include <math.h>

const size_t n_samples = 1024;
const float f = 1.f;
const float t_max_s = 1.f;
const float t_inc_s = t_max_s / n_samples;
__attribute__((unused)) float x = 0.f;

int main() {
  for (size_t n = 0; n < n_samples; ++n) {
    x = sinf(2 * M_PI * f * n * t_inc_s);
  }
  for (size_t n = 0; n < n_samples; ++n) {
    __attribute__((unused)) float y = cosf(2 * M_PI * f * n * t_inc_s);
  }
  return 0;
}
