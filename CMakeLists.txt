cmake_minimum_required(VERSION 3.10)
project(ChatServer VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add pthread for multithreading
find_package(Threads REQUIRED)

# --- SERVER BUILD ---
add_executable(chat_server
    src/main.cpp
    src/server.cpp
    src/utils.cpp
)
target_link_libraries(chat_server PRIVATE Threads::Threads)

# --- CLIENT BUILD (Add this) ---
add_executable(chat_client
    client/client.cpp
    src/utils.cpp 
)
target_link_libraries(chat_client PRIVATE Threads::Threads)