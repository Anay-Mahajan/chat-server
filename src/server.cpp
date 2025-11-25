#include "server.h"
#include "utils.h"
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include <string>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>
#include <mutex>
#include <csignal>
#include <vector>
namespace server
{
  void start(int port)
  {
    signal(SIGPIPE, SIG_IGN);
    int sd = socket(AF_INET, SOCK_STREAM, 0);
    if (sd < 0)
    {
      perror("socket");
      return;
    }
    sd_ = sd;
    int opt = 1;
    if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0)
    {
      perror("setsockopt");
      close(sd);
      return;
    }
    struct addrinfo hints;
    struct addrinfo *result;
    std::memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;
    int status = getaddrinfo(nullptr, std::to_string(port).c_str(), &hints, &result);
    if (status != 0)
    {
      std::cerr << "getaddrinfo: " << gai_strerror(status) << "\n";
      close(sd);
      return;
    }
    if (bind(sd, result->ai_addr, result->ai_addrlen) < 0)
    {
      perror("bind");
      freeaddrinfo(result);
      close(sd);
      return;
    }
    freeaddrinfo(result);
    if (listen(sd, SOMAXCONN) < 0)
    {
      perror("listen");
      close(sd);
      return;
    }
    std::cout << "Listening on port " << port << std::endl;
    accept_new_connection(sd_);
    std::cout<<"Total unsuccessfull message "<<count<<'\n';
    close(sd);
  }

  void accept_new_connection(int sd)
  {
    while(true){
      struct sockaddr_in client_addr;
      socklen_t client_len = sizeof(client_addr);
      int client_sd = accept(sd, (struct sockaddr *)&client_addr, &client_len);
      if (client_sd == -1)
      {
        perror("Accept failed");
        continue;
      }
      logMessage("New connection Accepted");
      std::thread(handle_client, client_sd).detach();
    }
  }
  void close_connection(int sd)
  {
    std::unique_lock<std::shared_mutex> lock(mp_mutex);
    auto it = sd_to_username.find(sd);
    if (it != sd_to_username.end())
    {
      username_to_sd.erase(it->second);
      sd_to_username.erase(it);
    }
  }
  bool safe_send(int sd, std::string data){
    ssize_t n = send(sd, data.c_str(), data.size(), MSG_NOSIGNAL);
    return n > 0;
  }

  void route_message(int from_sd, int to_sd, std::string message)
  {
      std::string from_user;
      {
      std::shared_lock<std::shared_mutex> lock(mp_mutex);
      auto it = sd_to_username.find(from_sd);
      if (it == sd_to_username.end())
        return;
      from_user = it->second;
    }
    std::string data = from_user + "->" + message + "\n";
    if (!safe_send(to_sd, data)){
      count++;
      logMessage("Couldn't Send Messsage"+std::to_string(count));
      std::set<int>::iterator it;
      {
        std::shared_lock<std::shared_mutex>lock(closed_mutex);
        it=closed_connection.find(to_sd);
      }
      if(it==closed_connection.end()){
        std::unique_lock<std::shared_mutex> lock(closed_mutex);
        closed_connection.insert(to_sd);
      }
    }
  }

  void broadcast(int from_sd, std::string message)
  {
    std::string from_user;
    std::vector<int> targets;{
      std::shared_lock<std::shared_mutex> lock(mp_mutex);
      auto it = sd_to_username.find(from_sd);
      if (it == sd_to_username.end())
        return;

      from_user = it->second;

      for (const auto &[user, sd] : username_to_sd)
      {
        if (sd != from_sd)
          targets.push_back(sd);
      }
    }
    std::string data =from_user + "->" + message + "\n";
    for (int sd : targets)
    {
      if (!safe_send(sd, data))
      {
        count++;
        logMessage("Couldn't Send Messsage"+std::to_string(count));
        std::set<int>::iterator it;
      {
        std::shared_lock<std::shared_mutex>lock(closed_mutex);
        it=closed_connection.find(sd);
      }
      if(it==closed_connection.end()){
        std::unique_lock<std::shared_mutex> lock(closed_mutex);
        closed_connection.insert(sd);
      }
      }
    }
  }

  void handle_route(int sd, std::string message)
  {
    int i = 1;
    ;
    std::string route = "";
    while (i < message.size() && message[i] != ' ')
    {
      route += message[i];
      i++;
    }
    if (i == message.size())
    {
      logMessage("Invalid Message\n");
      return;
    }
    i++;
    std::string raw_message = "";
    while (i < message.size())
    {
      raw_message += message[i];
      i++;
    }

    if (route == "advertize")
    {
      {
        std::unique_lock<std::shared_mutex> lock(mp_mutex);
        username_to_sd[raw_message] = sd;
        sd_to_username[sd] = raw_message;
      }
      logMessage(std::to_string(sd) + " " + raw_message);
    }
    else if (route == "all")
    {
      logMessage(std::to_string(sd) + " " + raw_message);
      broadcast(sd, raw_message);
    }
    else
    {
      int target_sd;

      {
        std::shared_lock<std::shared_mutex> lock(mp_mutex);
        auto it = username_to_sd.find(route);
        if (it == username_to_sd.end())
        {
          logMessage("Could Not find " + route);
          return;
        }
        target_sd = it->second;
      }
      logMessage(std::to_string(sd) + " " +std::to_string(target_sd) + " " +raw_message);
      route_message(sd, target_sd, raw_message);
    }
  }
  void handle_client(int client_sd)
  {
    char buffer[4096];
    std::string incoming;
    while (true)
    {
      memset(buffer, 0, sizeof(buffer));
      int bytes_received;
      bytes_received = recv(client_sd, buffer, sizeof(buffer), 0);
      if (bytes_received <= 0)
      {
        std::unique_lock<std::shared_mutex>lock(closed_mutex);
        closed_connection.insert(client_sd);
        break;
      }
      incoming.append(buffer, bytes_received);
      size_t pos;
      while ((pos = incoming.find('\n')) != std::string::npos)
      {
        std::string message = incoming.substr(0, pos);
        incoming.erase(0, pos + 1);
        if (!message.empty())
        {
          handle_route(client_sd, message);
        }
      }
    }
    close_connection(client_sd);
    close(client_sd);
  }
}