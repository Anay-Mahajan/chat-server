#include"../src/utils.h"
#include<iostream>
#include<string>
#include<cstring>
class client
{
private:
    int sd_;
    std::string username_;
public:
    client(int sd,std::string username){sd_=sd;username_=username;};
    ~client();
    void connect_to_server(int port);
    void disconnect();
    void send_message(std::string message);
    int get_sd(){return sd_;}
    std::string get_username(){return username_;}
};

