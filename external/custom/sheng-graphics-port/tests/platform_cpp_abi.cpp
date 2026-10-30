// Verify SDK-generated C++ objects against the ROM's actual platform libc++.
// This is a userspace ABI test; it does not access Binder or change security state.
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>
#include <cstdint>
#include <cstring>

int main()
{
    std::string shortString("ace5");
    std::string longString(128, 'H');
    shortString.append(longString).replace(0, 4, "HMOS");
    if (shortString.size() != 132 || shortString.substr(0, 4) != "HMOS") return 1;
    for (size_t i = 4; i < shortString.size(); ++i) if (shortString[i] != 'H') return 2;
    longString.reserve(4096);
    longString.append("-platform");
    if (longString.size() != 137 || longString.compare(128, 9, "-platform")) return 3;
    std::vector<std::string> values;
    for (unsigned i = 0; i < 257; ++i) values.emplace_back(std::to_string(i) + longString);
    for (unsigned i = 0; i < 257; ++i) if (values[i] != std::to_string(i) + longString) return 4;
    std::vector<uint32_t> numbers(1024);
    for (size_t i = 0; i < numbers.size(); ++i) numbers[i] = 1023 - i;
    std::sort(numbers.begin(), numbers.end());
    for (size_t i = 0; i < numbers.size(); ++i) if (numbers[i] != i) return 5;
    printf("PLATFORM_CPP_ABI_RESULT=0 string=%zu vector_u32=%zu pointer=%zu\n",
        sizeof(std::string), sizeof(std::vector<uint32_t>), sizeof(void*));
    return 0;
}
