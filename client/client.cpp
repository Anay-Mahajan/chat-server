#include "client.hpp"
#include <iostream>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include"arpa/inet.h"
void client::connect_to_server(int port)
{
    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);
    if (connect(sd_, (sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("connect failed");
        close(sd_);
        return;
    }
}
int main()
{
    std::string username;
    std::cout << "Enter your username: ";
    std::getline(std::cin, username);
    int sd = socket(AF_INET, SOCK_STREAM, 0);
    if (sd < 0) {
        perror("socket failed");
        return;
    }
    client C=client(sd,username);
    C.connect_to_server(8080);
}