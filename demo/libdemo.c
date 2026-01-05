__attribute__((visibility("default")))
int add(int a, int b) { return a + b; }

__attribute__((visibility("default")))
int mul(int a, int b) { return a * b; }

static int hidden(int x) { return x + 1; } // nie powinno być eksportowane
