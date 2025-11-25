#ifndef UTILS_H
#define UTILS_H

#include <string>
#include<mutex>

// Simple logging helper
void logMessage(const std::string &msg);
extern std::mutex util_cout;

#endif
