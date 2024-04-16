// ******function：对相机视频流实时显示******
// version:4.8 显示视频画面，退出方式为结束程序
#include "export.h"

static unsigned char imageBuffer[HEIGHT * WIDTH * 2];

void update_frame() {
    WSADATA wsaData;
    int sockfd;
    struct sockaddr_in servaddr, cliaddr;

    // 初始化Winsock
    if (WSAStartup(MAKEWORD(2,2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed." << std::endl;
        exit(EXIT_FAILURE);
    }

    // 创建套接字
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == SOCKET_ERROR) {
        std::cerr << "Socket creation failed: " << WSAGetLastError() << std::endl;
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    // 准备地址结构
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(PORT);

    // 绑定套接字
    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed: " << WSAGetLastError() << std::endl;
        closesocket(sockfd);
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    std::cout << "UDP server listening on port " << PORT << std::endl;

    std::vector<char> combinedData;
    int frameCount = 0;
    while (true) {
        char buffer[BUFFER_SIZE];
        int len = sizeof(cliaddr);

        // 接收数据
        int n = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&cliaddr, &len);
        if (n == SOCKET_ERROR) {
            std::cerr << "recvfrom failed: " << WSAGetLastError() << std::endl;
            continue;
        }

        // 检查帧头
        if (n == FRAME_HEADER_LENGTH) {
            //std::cout<<combinedData.size()<<std::endl;
            if (combinedData.size() >= TOTAL_DATA_SIZE) {
                memcpy(imageBuffer, combinedData.data(), TOTAL_DATA_SIZE);
                //std::cout<<combinedData.size()<<std::endl;
                

                
            }
            combinedData.clear();
            frameCount = 0;
            continue;
        }

        // 处理数据帧
        if (n == DATA_FRAME_SIZE && frameCount < EXPECTED_FRAMES) {
                frameCount++;
                
                int value = (buffer[2] << 8) | buffer[3];
                combinedData.insert(combinedData.end(), &buffer[DATA_OFFSET], &buffer[DATA_OFFSET] + DATA_LENGTH);
                //std::cout << "Value from 3rd and 4th bytes: " << value <<"  "<<frameCount<<std::endl;
                
            }
        
    }

    // 清理
    closesocket(sockfd);
    WSACleanup();

}
void start_stream()
{
    std::thread frameUpdateThread(update_frame);
    frameUpdateThread.join();

}


unsigned char* getImageBufferAddress() {
    return imageBuffer;
}

int main()
{
    start_stream();
}