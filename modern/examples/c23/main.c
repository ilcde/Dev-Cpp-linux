#include <stdio.h>

constexpr int answer = 42;
static_assert(answer == 42);

int main(void) {
    auto value = answer;
    printf("C23: %d\n", value);
    return 0;
}
