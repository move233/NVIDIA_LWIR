# function：界面显示与各个功能调用
# version:添加界面显示功能
# bug:电机再一个周期时间内会存在连续顺时针旋转两次，连续逆时针旋转两次的现象，这是什么原因？
# bug：反馈信息显示窗口滚动条不会自动往下，还需调整
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

# 定义目标检测函数
def RX(img0,img90):
        Data_re = np.stack((img0, img90), axis=2)
        nHeight_re, nWidth_re, _ = Data_re.shape
        Data_re1 = Data_re.reshape(nWidth_re*nHeight_re, 2).T
        X_mean = np.mean(Data_re1, axis=1, keepdims=True)
        X = Data_re1 - X_mean
        Sigma = np.dot(X, X.T) / X.shape[1]
        Sigma_inv = np.linalg.inv(Sigma)
        D = np.zeros(X.shape[1])
        for m in range(X.shape[1]):
            D[m] = np.dot(np.dot(X[:, m].T, Sigma_inv), X[:, m])

        img_re = D.reshape(nHeight_re, nWidth_re)
        min = np.min(img_re)
        max = np.max(img_re)
        # 转换为8位来显示
        img_re1 = ((img_re - min) / (max - min) * 255).astype(np.uint8)
        return img_re1



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
        self.frame_function = None
        self.display()
        # 状态返回区域设置为只读不允许编辑
        self.feedback_information.setReadOnly(True)
        # 连接按钮等控件的信号与槽
        self.connect_button.clicked.connect(self.START_stream)
        self.detection_button.clicked.connect(self.detection)
        self.capture_button.clicked.connect(self.capture)
    
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
        if self.frame_base is not None:
            img_base = QImage(self.frame_base.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
            pixmap_base = QPixmap.fromImage(img_base)
            self.video_base.setPixmap(pixmap_base)
            
        if self.frame_function is not None:
            img_function = QImage(self.frame_function.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
            pixmap_function = QPixmap.fromImage(img_function)
            self.video_function.setPixmap(pixmap_function)
    
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
            cv2.waitKey(3)
    
    def detection(self):
        self.detection_running = True
        def detection_loop(main_app_instance):
            while main_app_instance.detection_running:
                main_app_instance.send('0ma00000000\r')
                time.sleep(0.5)
                I90 = main_app_instance.frame_base
                main_app_instance.send('0sj00008C00\r')

                main_app_instance.send('0fw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = main_app_instance.frame_base
                main_app_instance.frame_function = RX(I0, I90)
                main_app_instance.display()
                main_app_instance.feedback_information.append("检测成功")
                time.sleep(1)

                main_app_instance.send('0bw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = main_app_instance.frame_base
                main_app_instance.frame_function = RX(I0, I90)
                main_app_instance.display()
                main_app_instance.feedback_information.append("检测成功")
                time.sleep(1)
        
        threading.Thread(target=detection_loop, args=(self,)).start()

    
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
