#include <iostream>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <thread>

#define BUFFER_SIZE 65507*3
#define DATA_FRAME_SIZE 63504
#define DATA_OFFSET 12
#define DATA_LENGTH 63488
#define FRAME_HEADER_LENGTH 16
#define EXPECTED_FRAMES 11
#define TOTAL_DATA_SIZE 655360
#define LAST_DATA_LENGTH 20480
class UDP_LWIR_CAMERA{
    private:
        bool run_flag;
    public:
        WSADATA wsaData;
        int sockfd;
        struct sockaddr_in servaddr, cliaddr;
        char output_data[640*512*2];
        char data_buffer[640*512*2];
        UDP_LWIR_CAMERA();
        void UDP_INIT(int port);
        void UPDATE_FRAME();
        void STOP_UPDATE_FRAME();
        ~UDP_LWIR_CAMERA();
        
        
};
extern "C"{
    __declspec(dllexport) void UDP_INIT(int port);
    __declspec(dllexport) void START_UPDATE_FRAME_THREAD();
    __declspec(dllexport) void STOP_UPDATE_FRAME_THREAD();
    __declspec(dllexport) const char* GET_CURRENT_FRAME();
}