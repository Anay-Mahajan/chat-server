#include"../src/utils.h"
#include<iostream>
#include<string>
#include<cstring>
#include<mutex>
class client
{
private:
    int sd_;
    std::string username_;
    std::mutex cout_lock;
public:
    client(int sd,std::string username);
    ~client();
    void connect_to_server(int port);
    void disconnect();
    void send_message(std::string message);
    int get_sd(){return sd_;}
    std::string get_username(){return username_;}
    void handle_send();
    void handle_recv();
    void print_message(std::string mess);
};

