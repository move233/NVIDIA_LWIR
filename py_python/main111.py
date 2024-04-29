# function：界面显示与各个功能调用
# version:添加界面显示功能
# bug:电机再一个周期时间内会存在连续顺时针旋转两次，连续逆时针旋转两次的现象，这是什么原因？
# bug：反馈信息显示窗口滚动条不会自动往下，还需调整
import ctypes
import threading
import numpy as np
import cv2
import datetime
import serial
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget,QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from LWIR_NVIDIAui111 import Ui_LWIR
import sys
import time
import os


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
class MainWindow(QMainWindow,Ui_LWIR):
    # 初始化
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setupUi(self)
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
        self.path_file.clicked.connect(self.pathfile)
        self.angle_display.currentIndexChanged.connect(self.angle_status)
        self.download_button.clicked.connect(self.download_capture)
        self.angle_flag=None
        self.angle_N=None
        self.folder_path = None

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

    # 保存图像-打开图像保存设置窗口
    def pathfile(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
        if self.folder_path:
            self.path_display.setText(self.folder_path)

    def angle_status(self,index):
        self.angle_flag = index#记录下当前索引，以便于采集时驱动电机用
        text_download = "当前偏振通道："+ str(index)+"  "+self.angle_display.currentText()
        self.feedback_information.append(text_download)
        # return index

    def download_capture(self):
        self.capture_running = True
        def capture_loop(main_app_instance):
            while main_app_instance.capture_running:
                #90
                if main_app_instance.angle_flag == 1 :
                    send_data = '0sj00008C00\r'
                    main_app_instance.angle_N = 3
                # 60
                elif main_app_instance.angle_flag == 2 :
                    send_data = '0sj00005D55\r'
                    main_app_instance.angle_N = 4
                # 45
                elif main_app_instance.angle_flag == 3 :
                    send_data = '0sj00004600\r'
                    main_app_instance.angle_N = 5
                # 30
                elif main_app_instance.angle_flag == 4 :
                    send_data = '0sj00002EAB\r'
                    main_app_instance.angle_N = 7
                # 5
                elif main_app_instance.angle_flag == 5 :
                    send_data = '0sj000007C7\r'
                    main_app_instance.angle_N = 37
                main_app_instance.capture_running=False
                current_time = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
                folder_name = str(main_app_instance.angle_flag) + '_' + current_time+'/'
                print(folder_name)
                os.makedirs(main_app_instance.folder_path + '/'+folder_name)
                text_folder = "文件夹" + format(folder_name) + "创建成功"
                main_app_instance.feedback_information.append(text_folder)
                #电机切换回到零位
                main_app_instance.send(send_data)
                time.sleep(2)
                main_app_instance.send('0ma00000000\r')
                time.sleep(1)
                if main_app_instance.frame_base is not None:
                    save_path = os.path.join(main_app_instance.folder_path, folder_name, '1.bmp')
                    cv2.imwrite(save_path, main_app_instance.frame_base)
                # 设置相对转动角度
                
                n = 2
                while (n<=main_app_instance.angle_N):
                    time.sleep(1)
                    main_app_instance.send('0fw\r')#顺时针转动
                    if main_app_instance.frame_base is not None:
                        save_path = os.path.join(main_app_instance.folder_path, folder_name, str(n) + '.bmp')
                        cv2.imwrite(save_path, main_app_instance.frame_base)
                    n=n+1
                if n==main_app_instance.angle_N+1:
                    main_app_instance.send('0ma00000000\r')
                    text_download = "采集完成"
                    main_app_instance.feedback_information.append(text_download)

        threading.Thread(target=capture_loop, args=(self,)).start()



if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

