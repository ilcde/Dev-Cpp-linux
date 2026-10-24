#include <iostream>

template <class... T>
auto first(T... values) {
    return values...[0];
}

int main() {
    std::cout << "C++26 pack indexing: " << first(42, 7, 3) << '\n';
}
