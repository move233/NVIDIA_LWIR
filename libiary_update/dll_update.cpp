#include "dll_update.h"
// -----------------------------
// -----------------------------
// UDP_LWIR_CAMERA类的实现
// -----------------------------
// -----------------------------

//UDP_LWIR_CAMERA类构造函数
UDP_LWIR_CAMERA::UDP_LWIR_CAMERA()
{
    std::memset(data_buffer, 0, sizeof(data_buffer));
    std::memset(output_data, 0, sizeof(output_data));
    run_flag=false;
}

//初始化UDP监听端口
void UDP_LWIR_CAMERA::UDP_INIT(int port)
{
    //初始化Winsock
    if (WSAStartup(MAKEWORD(2,2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed." << std::endl;
        exit(EXIT_FAILURE);
    }
    //创建套接字
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == SOCKET_ERROR) {
        std::cerr << "Socket creation failed: " << WSAGetLastError() << std::endl;
        WSACleanup();
        exit(EXIT_FAILURE);
    }
    // 准备地址结构
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(port);
    std::cout<<"ready to receive data"<<std::endl;
    run_flag=true;

    //绑定套接字
    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed: " << WSAGetLastError() << std::endl;
        closesocket(sockfd);
        WSACleanup();
        exit(EXIT_FAILURE);
    }
}

//update_buffer 方法实现
void UDP_LWIR_CAMERA::UPDATE_FRAME()
{
    int frameCount = 0;
    while(run_flag)
    {
        char buffer[BUFFER_SIZE];
        int len = sizeof(cliaddr);
        int n = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&cliaddr, &len);
        if (n == SOCKET_ERROR) {
            std::cerr << "recvfrom failed: " << WSAGetLastError() << std::endl;
            continue;
        }

        if (n == FRAME_HEADER_LENGTH) {
            // 检测到新的帧头，准备处理新的完整帧
            frameCount = 0;
            std::memset(data_buffer, 0, sizeof(data_buffer));  // 清空目标缓冲区
            //std::cout << "Frame header detected" << std::endl;
        }

        if (n == DATA_FRAME_SIZE || n == LAST_DATA_LENGTH) {
            frameCount++;
            int offset;
            int copy_length;

            // 如果是最后一帧，使用不同的 `DATA_LENGTH`
            if (frameCount == EXPECTED_FRAMES) {
                offset = (frameCount - 1) * DATA_LENGTH;
                copy_length = LAST_DATA_LENGTH;
            } else {
                offset = (frameCount - 1) * DATA_LENGTH;
                copy_length = DATA_LENGTH;
            }

            // 将数据帧复制到目标缓冲区
            std::memcpy(&data_buffer[offset], &buffer[DATA_OFFSET], copy_length);
            //std::cout << "Frame data " << frameCount << std::endl;

            // 当收集到预期的 11 个数据帧时，完整帧已组装完成
            if (frameCount == EXPECTED_FRAMES) {
                //std::cout << "Complete frame assembled" << std::endl;
                std::memcpy(output_data, data_buffer, sizeof(data_buffer));
            }
        }
    }
    
}

//停止更新数据
void UDP_LWIR_CAMERA::STOP_UPDATE_FRAME()
{
    run_flag=false;
    closesocket(sockfd);
    WSACleanup();
}

//析构函数
UDP_LWIR_CAMERA::~UDP_LWIR_CAMERA()
{
    std::cout<<"stop"<<std::endl;
}


// -----------------------------
// -----------------------------
//声明静态类
// -----------------------------
// -----------------------------
static UDP_LWIR_CAMERA camera;

// -----------------------------
// -----------------------------
//初始化UDP端口
// -----------------------------
// -----------------------------
void UDP_INIT(int port)
{
    camera.UDP_INIT(port);
}

// -----------------------------
// -----------------------------
//建立更新数据线程
// -----------------------------
// -----------------------------
void START_UPDATE_FRAME_THREAD()
{
    std::thread frame_thread(&UDP_LWIR_CAMERA::UPDATE_FRAME, &camera);
    frame_thread.detach();
    //camera.UPDATE_FRAME();
}

// -----------------------------
// -----------------------------
//获取当前帧
// -----------------------------
// -----------------------------
const char* GET_CURRENT_FRAME()
{
    return camera.output_data;
}
// -----------------------------
// -----------------------------
//关闭线程
// -----------------------------
// -----------------------------
void STOP_UPDATE_FRAME_THREAD()
{
    camera.STOP_UPDATE_FRAME();
}
