#include "server.h"
#include "utils.h"
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include <cstring>
#include <iostream>
 namespace server{
    void start(int port){
        int sd=socket(PF_INET,SOCK_STREAM,0);
        struct addrinfo hints{};
        struct addrinfo *resutlt;
        memset(&hints, 0, sizeof(hints));
        hints.ai_family=PF_INET;
        hints.ai_socktype=SOCK_STREAM;
        hints.ai_flags=AI_PASSIVE;
        int status =getaddrinfo(NULL,"8080",&hints,&resutlt);
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
            std::cout<<"Listening to Port 8080\n";
         }
         for(;;){
          struct sockaddr_in client_addr;
         socklen_t client_len = sizeof(client_addr);
         int client_sd = accept(sd, (struct sockaddr*)&client_addr, &client_len);
         if (client_sd == -1) {
            perror("Accept failed");
            continue;
         }
          const char *response =
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 12\r\n"
                "\r\n"
                "Hello World!";

            send(client_sd, response, strlen(response), 0);
         std::cout << "New connection accepted.\n";
        close(client_sd); 
      }
       close(sd);
    }

   
 }