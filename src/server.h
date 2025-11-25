#ifndef SERVER_H
#define SERVER_H
#include<map>
#include<shared_mutex>
#include<string>
#include<set>
namespace server {
    static int sd_;
    static int count=0;
    static std::shared_mutex mp_mutex;
    static std::shared_mutex closed_mutex;
    static std::set<int>closed_connection;
    static std::map<std::string,int>username_to_sd;
    static std::map<int,std::string>sd_to_username;
    void start(int port);
    void route_message(int client_sd1,int client_sd2,std::string message);
    void close_connection(int client_sd);
    void handle_client(int clinet_sd);
    void accept_new_connection(int sd);
    void broadcast(int sd_from,std::string message);
    void handle_route(int sd1,std::string message);
}

#endif
