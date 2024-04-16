#include <iostream>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <cstring>
#include <vector>
#include <thread>
#include <atomic>
#include <thread>
#include <chrono>
#include <numeric>
#include <opencv2/opencv.hpp>
#include <Eigen/Dense>

#define PORT 32345
#define BUFFER_SIZE 65507*3
#define DATA_FRAME_SIZE 63504
#define DATA_OFFSET 12
#define DATA_LENGTH 63488
#define FRAME_HEADER_LENGTH 16
#define EXPECTED_FRAMES 11
#define TOTAL_DATA_SIZE 655360 // 640x512x2 bytes
#define PIXEL_SIZE 2
#define WIDTH 640
#define HEIGHT 512
#define SERIAL COM8



extern "C"
{
    __declspec(dllexport) void start_stream();//启动视频流
    __declspec(dllexport) unsigned char* getImageBufferAddress();//获取数据地址
    __declspec(dllexport) void stop_stream();//结束视频流
}