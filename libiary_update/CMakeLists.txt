cmake_minimum_required(VERSION 3.15)
project(libiary_update)
set(CXX_STANDARD_REQUIRED 11)
file(GLOB SRC ${CMAKE_CURRENT_SOURCE_DIR}/dll_update.cpp)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/)
# add_executable(main ${SRC})
add_library(udp_dll SHARED ${SRC})
target_link_libraries(udp_dll  ws2_32)