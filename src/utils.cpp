#include "utils.h"
#include <iostream>
#include <ctime>

void logMessage(const std::string &msg) {
    std::time_t now = std::time(nullptr);
    std::string timeStr = std::ctime(&now);
    timeStr.pop_back(); // remove trailing newline
    std::cout << "[" << timeStr << "] " << msg << std::endl;
}
