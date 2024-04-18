# function：界面显示与各个功能调用
# version:添加界面显示功能
import ctypes
import threading
import numpy as np
import cv2
import time
import serial
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
from LWIR_NVIDIAui import Ui_MainWindow
import sys
import time


# ******初始定义******
# 加载 DLL
dll = ctypes.WinDLL('E:/vscode_c++_project/nvidia_LWIR/build/camera2.dll', winmode=0)
# 定义返回类型
dll.getImageBufferAddress.argtypes = []  # 无参数
dll.getImageBufferAddress.restype = ctypes.POINTER(ctypes.c_ubyte) 


# ******gui设计******
class MainApp(QMainWindow, Ui_MainWindow):
    # 初始化
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置UI
        self.ser=serial.Serial()
        self.port_open_recv("COM8", 9600)   
        # 视频显示区域
        self.detect_flag=0
        self.frame_base = None
        self.old_frame=None
        self.new_frame=None
        self.frame_function = None
        self.display()
        # 状态返回区域设置为只读不允许编辑
        self.feedback_information.setReadOnly(True)
        # 连接按钮等控件的信号与槽
        self.connect_button.clicked.connect(self.START_stream)
        self.detection_button.clicked.connect(self.detection)
        self.capture_button.clicked.connect(self.capture)
        # self.frame_timer = QTimer(self)  # 计时器，用来控制update_frame的循环调用的频率，在start_camera函数中启动这个计时器，这里只做初始化
        # self.frame_timer.timeout.connect(self.display)
        # self.detect_timer=QTimer(self)
        # self.detect_timer.timeout.connect(self.detection)
    
    def port_open_recv(self, com, baud):
        self.ser.port = com
        self.ser.baudrate = baud
        self.ser.bytesize = 8
        self.ser.stopbits = 1
        self.ser.parity = "N"
        self.ser.open()

    def send(self,send_data):
        if self.ser.isOpen():
            self.ser.write(send_data.encode('utf-8'))
            text_serial = send_data + "发送成功"
            self.feedback_information.append(text_serial)
        else:
            text_serial = "发送失败！串口未打开"
            self.feedback_information.append(text_serial)

    def display(self):
        # h, w = self.frame_base.shape
        # bytes_per_line = w
        # while finished:
        if self.frame_base is not None:
            img_base = QImage(self.frame_base.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
            pixmap_base = QPixmap.fromImage(img_base)
            self.video_base.setPixmap(pixmap_base)
            
            # if not finished:
            #     break
        # if self.function_base is not None:
        #     img_function = QImage(self.frame_function.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
        #     # scaled_pixmap2 = pixmap2.scaled(self.video_function.size(), Qt.AspectRatioMode.KeepAspectRatio)
        #     pixmap_function = QPixmap.fromImage(img_function)
        #     self.video_function.setPixmap(pixmap_function)

    def START_stream(self):
        # 启动视频流线程
        t = threading.Thread(target = dll.start_stream)
        t.start()
        time.sleep(0.5)
        buffer_size = 640*512
        # 获取图像缓冲区地址
        buffer_address = dll.getImageBufferAddress()
        buffer = (ctypes.c_uint16 * buffer_size).from_address(ctypes.addressof(buffer_address.contents))
        image = np.frombuffer(buffer, dtype=np.uint16).reshape((512, 640))
        text_start = "相机已连接"
        self.feedback_information.append(text_start)
        while True:
            min_val = np.min(image)
            max_val = np.max(image)
            # 转换为8位来显示
            image_normalized = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
            self.frame_base = image_normalized
            # 在界面中显示
            self.display()
            # self.frame_timer.start(30)
            cv2.waitKey(3)
    
    def detection(self):
        def send_instructions():
            while True:
                self.send('0ma00000000\r\n')
                time.sleep(0.3)
                I0 = self.frame_base

                text_capture = "0°图像已采集"
                self.feedback_information.append(text_capture)
                time.sleep(1)

                self.send('0mr00008C00\r\n')
                time.sleep(0.3)
                I90 = self.frame_base
                text_capture = "90°图像已采集"
                self.feedback_information.append(text_capture)

                # Data_re = np.stack((I0, I90), axis=2)
                # nHeight_re, nWidth_re, _ = Data_re.shape
                # Data_re1 = Data_re.reshape(nWidth_re*nHeight_re, 2).T
                # r1_re = RX(Data_re1)
                # img_re = r1_re.reshape(nHeight_re, nWidth_re)
                # self.frame2 = img_re
                time.sleep(1)
        threading.Thread(target=send_instructions).start()

    # 目标检测
    def RX(X):
        X_mean = np.mean(X, axis=1, keepdims=True)
        X = X - X_mean
        Sigma = np.dot(X, X.T) / X.shape[1]
        Sigma_inv = np.linalg.inv(Sigma)
        D = np.zeros(X.shape[1])
        for m in range(X.shape[1]):
            D[m] = np.dot(np.dot(X[:, m].T, Sigma_inv), X[:, m])

        return D
    
    # 保存图像
    def capture(self):
        # if self.frame1 is not None:
        #     current_time = datetime.now()
        #     file_name = current_time.strftime("%H%M%S") + ".jpg"
        #     cv2.imwrite(file_name, self.frame1)
        # print("capture")
        text_start = "图片已保存"
        self.feedback_information.append(text_start)


if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

