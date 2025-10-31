#include "server.h"
#include "utils.h"

#include <iostream>
#include <cstring>
#include <unistd.h>        // for close()
#include <netinet/in.h>    // for sockaddr_in
#include <sys/socket.h>    // for socket functions

namespace server {

void start(int port) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("socket failed");
        return;
    }

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY; // listen on all interfaces
    address.sin_port = htons(port);

    // Allow immediate reuse of the port after restarting
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("bind failed");
        close(server_fd);
        return;
    }

    if (listen(server_fd, 5) < 0) {
        perror("listen failed");
        close(server_fd);
        return;
    }

    logMessage("Server started. Listening on port " + std::to_string(port) + "...");

    while (true) {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) {
            perror("accept failed");
            continue;
        }
        logMessage("New client connected.");
        close(client_fd);  // for now, just close immediately
    }

    close(server_fd);
}

} // namespace server
