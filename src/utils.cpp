#include "utils.h"
#include <iostream>
#include <ctime>
#include<mutex>
std::mutex util_cout;
void logMessage(const std::string &msg) {
    std::time_t now = std::time(nullptr);
    std::string timeStr = std::ctime(&now);
    timeStr.pop_back(); // remove trailing newline
    std::lock_guard<std::mutex>lock(util_cout);
    std::cout << "[" << timeStr << "] " << msg << std::endl;
}
