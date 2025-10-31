#include "server.h"
#include <iostream>

int main() {
    int port = 8080;
    std::cout << "Starting server on port " << port << "..." << std::endl;
    server::start(port);
    return 0;
}
