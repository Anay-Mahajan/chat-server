#include "server.h"
#include "utils.h"
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include <string>
#include<cstring>
#include <iostream>
#include <string>
#include<thread>
#include<mutex>
 namespace server{
    void start(int port){
        int sd=socket(PF_INET,SOCK_STREAM,0);
        sd_=sd;
        struct addrinfo hints{};
        struct addrinfo *resutlt;
        memset(&hints, 0, sizeof(hints));
        hints.ai_family=PF_INET;
        hints.ai_socktype=SOCK_STREAM;
        hints.ai_flags=AI_PASSIVE;
        int status =getaddrinfo(NULL,std::to_string(port).c_str(),&hints,&resutlt);
        if(status==-1){
         std::cout<<"Handle Address Info\n";
        }
       status=bind(sd,resutlt->ai_addr,resutlt->ai_addrlen);
       if(status==-1){
         std::cout<<"Handle Bind\n";
       }
         status =listen(sd,10);
         if(status==-1){
            std::cout<<"Handle Listen\n";
         }
         else{
            std::cout<<"Listening on Port 8080\n";
         }
         accept_new_connection(sd);
         close(sd);
    }
    void accept_new_connection(int sd){
      for(;;){
          struct sockaddr_in client_addr;
          socklen_t client_len = sizeof(client_addr);
          int client_sd = accept(sd, (struct sockaddr*)&client_addr, &client_len);
         if (client_sd == -1) {
            perror("Accept failed");
            continue;
         }
         logMessage("New connection Accepted");  
         std::thread(handle_client,client_sd).detach();
      }
    }
    void route_message(int sd_1,int sd_2,std::string message){
      std::string data = "@" + sd_to_username[sd_1] + " " + message;
      send(sd_2, data.c_str(), data.length(), 0);
    }
    void broadcast(int sd_from,std::string message){
      std::string data = "@" +sd_to_username[sd_from]+" "+message;
      for(auto&[user,sd]:username_to_sd){
         if(sd!=sd_from)   send(sd,data.c_str(),data.length(),0);
      }
    }
    void handle_route(int sd,std::string message){
       int i=1;;
       std::string route="";
       while(message[i]!=' '){
         route+=message[i];
          i++;
       }
       i++;
       std::string raw_message="";
       while (i<message.size()){
         raw_message+=message[i];
         i++;
       }
       
       if(route=="advertize"){
         username_to_sd[raw_message]=sd;
         sd_to_username[sd]=raw_message;
         logMessage(std::to_string(sd)+" "+raw_message);
       }
       else if(route=="all"){
         logMessage(std::to_string(sd)+" "+raw_message);
         broadcast(sd,raw_message);
       }
       else{
         if(username_to_sd.find(route)!=username_to_sd.end()){
            logMessage(std::to_string(sd)+" "+std::to_string(username_to_sd[route])+" "+raw_message);
            route_message(sd,username_to_sd[route],raw_message);
         }
         else{
            logMessage("Could Not find "+route);
         }
       }
    }
    void handle_client(int client_sd){
       char buffer[4096];
       while (true){
          memset(buffer, 0, sizeof(buffer));
          int bytes_received;
          bytes_received = recv(client_sd, buffer, sizeof(buffer), 0);
          if (bytes_received > 0){
            std::string message= std::string(buffer,bytes_received);
            std::thread(handle_route,client_sd,message).detach();    
          }
       }
    }
 }