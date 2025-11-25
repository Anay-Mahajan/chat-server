#include "client.hpp"
#include <iostream>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include"arpa/inet.h"
#include<thread>
#include<mutex>
void client::send_message(std::string message){
    std::string final_msg = message; 
     send(sd_, final_msg.c_str(), final_msg.length(), 0);
}
void client::handle_send(){
    while (true)
    {
        std::string line ;
        std::getline(std::cin,line);
        if(line!="") send_message(line);
    }
    
}
void client::print_message(std::string mess){
    std::lock_guard<std::mutex>lock(cout_lock);
    std::cout <<mess << std::endl;
}
void client::handle_recv(){
    char buffer[4096];
    while(true){
        memset(buffer, 0, sizeof(buffer));
        int bytes_received;     
        bytes_received = recv(sd_, buffer, sizeof(buffer), 0);
        if (bytes_received <= 0) {
            std::cout << "Server disconnected." << std::endl;
            break;
        }
        std::string mess(buffer,bytes_received);
       print_message(mess);
    }
}
void client::connect_to_server(int port)
{
    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, "192.168.1.2", &server_addr.sin_addr);
    if (connect(sd_, (sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("connect failed");
        close(sd_);
        return;
    }
    send_message("@advertize "+username_);
    std::thread t1(&client::handle_send, this);
    std::thread t2(&client::handle_recv, this);

    if(t1.joinable()) t1.join();
    if(t2.joinable()) t2.join();
}
client::~client(){
    send_message("@all"+username_+" Left The Chat");
    close(sd_);
}
void client::disconnect(){
    send_message("@all"+username_+" Left the Chat");
    close(sd_);
}
client::client(int sd,std::string username)
{
    sd_=sd;
    username_=username;
}
int main()
{
    std::string username;
    std::cout << "Enter your username: ";
    std::getline(std::cin, username);
    int sd = socket(AF_INET, SOCK_STREAM, 0);
    if (sd < 0) {
        perror("socket failed");
        return 0;
    }
    client C=client(sd,username);
    C.connect_to_server(8080);
    return 0;
}